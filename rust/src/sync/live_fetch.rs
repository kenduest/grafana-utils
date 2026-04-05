//! Thin wrappers around the shared sync live read layer.

use std::iter::FromIterator;

use crate::alert::build_rule_import_payload;
use crate::common::{message, Result};
#[cfg(test)]
use crate::grafana_api::{
    fetch_sync_live_availability_with_request, fetch_sync_live_resource_specs_with_request,
};
use crate::grafana_api::{merge_sync_live_availability, SyncLiveClient};
use crate::sync::{
    append_unique_strings, normalize_alert_managed_fields,
    normalize_alert_resource_identity_and_title, require_json_object,
};
use serde_json::{Map, Value};

fn build_live_alert_resource_spec(sync_kind: &str, body: Map<String, Value>) -> Result<Value> {
    let (identity, title) = normalize_alert_resource_identity_and_title(sync_kind, &body)?;
    Ok(serde_json::json!({
        "kind": sync_kind,
        "uid": if sync_kind == "alert-contact-point" { identity.clone() } else { String::new() },
        "name": if matches!(sync_kind, "alert-mute-timing" | "alert-template") { identity.clone() } else { String::new() },
        "title": title,
        "managedFields": normalize_alert_managed_fields(&body),
        "body": body,
    }))
}

pub(crate) fn merge_availability(base: Option<Value>, extra: &Value) -> Result<Value> {
    merge_sync_live_availability(base, extra)
}

pub(crate) fn fetch_live_resource_specs_with_client(
    client: &SyncLiveClient<'_>,
    page_size: usize,
) -> Result<Vec<Value>> {
    let mut specs = Vec::new();

    for folder in client.list_folders()? {
        let uid = folder
            .get("uid")
            .and_then(Value::as_str)
            .map(str::trim)
            .unwrap_or("");
        if uid.is_empty() {
            continue;
        }
        let title = folder
            .get("title")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .unwrap_or(uid);
        let mut body = Map::new();
        body.insert("title".to_string(), Value::String(title.to_string()));
        if let Some(parent_uid) = folder
            .get("parentUid")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            body.insert(
                "parentUid".to_string(),
                Value::String(parent_uid.to_string()),
            );
        }
        specs.push(serde_json::json!({
            "kind": "folder",
            "uid": uid,
            "title": title,
            "body": body,
        }));
    }

    for summary in client.list_dashboard_summaries(page_size)? {
        let uid = summary
            .get("uid")
            .and_then(Value::as_str)
            .map(str::trim)
            .unwrap_or("");
        if uid.is_empty() {
            continue;
        }
        let dashboard_wrapper = client.fetch_dashboard(uid)?;
        let wrapper = require_json_object(&dashboard_wrapper, "Grafana dashboard payload")?;
        let dashboard = wrapper
            .get("dashboard")
            .ok_or_else(|| message(format!("Unexpected dashboard payload for UID {uid}.")))?;
        let body = require_json_object(dashboard, "Grafana dashboard body")?;
        let mut normalized = body.clone();
        normalized.remove("id");
        let title = normalized
            .get("title")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .unwrap_or(uid);
        specs.push(serde_json::json!({
            "kind": "dashboard",
            "uid": uid,
            "title": title,
            "body": normalized,
        }));
    }

    for datasource in client.list_datasources()? {
        let uid = datasource
            .get("uid")
            .and_then(Value::as_str)
            .map(str::trim)
            .unwrap_or("");
        let name = datasource
            .get("name")
            .and_then(Value::as_str)
            .map(str::trim)
            .unwrap_or("");
        if uid.is_empty() && name.is_empty() {
            continue;
        }
        let title = if name.is_empty() { uid } else { name };
        let mut body = Map::new();
        body.insert("uid".to_string(), Value::String(uid.to_string()));
        body.insert("name".to_string(), Value::String(title.to_string()));
        body.insert(
            "type".to_string(),
            datasource
                .get("type")
                .cloned()
                .unwrap_or(Value::String(String::new())),
        );
        body.insert(
            "access".to_string(),
            datasource
                .get("access")
                .cloned()
                .unwrap_or(Value::String(String::new())),
        );
        body.insert(
            "url".to_string(),
            datasource
                .get("url")
                .cloned()
                .unwrap_or(Value::String(String::new())),
        );
        body.insert(
            "isDefault".to_string(),
            datasource
                .get("isDefault")
                .cloned()
                .unwrap_or(Value::Bool(false)),
        );
        if let Some(json_data) = datasource.get("jsonData").and_then(Value::as_object) {
            if !json_data.is_empty() {
                body.insert("jsonData".to_string(), Value::Object(json_data.clone()));
            }
        }
        specs.push(serde_json::json!({
            "kind": "datasource",
            "uid": uid,
            "name": title,
            "title": title,
            "body": body,
        }));
    }

    for rule in client.list_alert_rules()? {
        let body = build_rule_import_payload(&rule)?;
        let uid = body
            .get("uid")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .ok_or_else(|| message("Live alert rule payload is missing uid."))?;
        let title = body
            .get("title")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .unwrap_or(uid);
        specs.push(serde_json::json!({
            "kind": "alert",
            "uid": uid,
            "title": title,
            "body": body,
        }));
    }

    for contact_point in client.list_contact_points()? {
        specs.push(build_live_alert_resource_spec(
            "alert-contact-point",
            contact_point,
        )?);
    }

    for mute_timing in client.list_mute_timings()? {
        specs.push(build_live_alert_resource_spec(
            "alert-mute-timing",
            mute_timing,
        )?);
    }

    specs.push(build_live_alert_resource_spec(
        "alert-policy",
        client.get_notification_policies()?,
    )?);

    for template in client.list_templates()? {
        let name = template
            .get("name")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .ok_or_else(|| message("Live template payload is missing name."))?;
        specs.push(build_live_alert_resource_spec(
            "alert-template",
            client.get_template(name)?,
        )?);
    }

    Ok(specs)
}

#[cfg(test)]
pub(crate) fn fetch_live_resource_specs_with_request<F>(
    request_json: F,
    page_size: usize,
) -> Result<Vec<Value>>
where
    F: FnMut(reqwest::Method, &str, &[(String, String)], Option<&Value>) -> Result<Option<Value>>,
{
    fetch_sync_live_resource_specs_with_request(request_json, page_size)
}

pub(crate) fn fetch_live_availability_with_client(client: &SyncLiveClient<'_>) -> Result<Value> {
    let mut availability = Map::from_iter(vec![
        ("datasourceUids".to_string(), Value::Array(Vec::new())),
        ("datasourceNames".to_string(), Value::Array(Vec::new())),
        ("pluginIds".to_string(), Value::Array(Vec::new())),
        ("contactPoints".to_string(), Value::Array(Vec::new())),
    ]);

    let mut uids = Vec::new();
    let mut names = Vec::new();
    for datasource in client.list_datasources()? {
        if let Some(uid) = datasource
            .get("uid")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            uids.push(uid.to_string());
        }
        if let Some(name) = datasource
            .get("name")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            names.push(name.to_string());
        }
    }
    append_unique_strings(
        availability
            .get_mut("datasourceUids")
            .and_then(Value::as_array_mut)
            .expect("datasourceUids should be array"),
        &uids,
    );
    append_unique_strings(
        availability
            .get_mut("datasourceNames")
            .and_then(Value::as_array_mut)
            .expect("datasourceNames should be array"),
        &names,
    );

    let ids = client
        .list_plugins()?
        .iter()
        .filter_map(|plugin| plugin.get("id").and_then(Value::as_str))
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(str::to_string)
        .collect::<Vec<_>>();
    append_unique_strings(
        availability
            .get_mut("pluginIds")
            .and_then(Value::as_array_mut)
            .expect("pluginIds should be array"),
        &ids,
    );

    let mut contact_points = Vec::new();
    for item in client.list_contact_points()? {
        if let Some(name) = item
            .get("name")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            contact_points.push(name.to_string());
        }
        if let Some(uid) = item
            .get("uid")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            contact_points.push(uid.to_string());
        }
    }
    append_unique_strings(
        availability
            .get_mut("contactPoints")
            .and_then(Value::as_array_mut)
            .expect("contactPoints should be array"),
        &contact_points,
    );

    Ok(Value::Object(availability))
}

#[cfg(test)]
pub(crate) fn fetch_live_availability_with_request<F>(request_json: F) -> Result<Value>
where
    F: FnMut(reqwest::Method, &str, &[(String, String)], Option<&Value>) -> Result<Option<Value>>,
{
    fetch_sync_live_availability_with_request(request_json)
}
