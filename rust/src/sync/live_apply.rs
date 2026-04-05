//! Thin wrappers around the shared sync live apply layer.

use crate::alert::{
    build_contact_point_import_payload, build_mute_timing_import_payload,
    build_policies_import_payload, build_rule_import_payload, build_template_import_payload,
};
use crate::common::{message, Result};
#[cfg(test)]
use crate::grafana_api::execute_sync_live_apply_with_request;
use crate::grafana_api::SyncLiveClient;
use crate::sync::apply_contract::SyncApplyOperation;
use serde_json::Value;

fn apply_folder_operation_with_client(
    client: &SyncLiveClient<'_>,
    operation: &SyncApplyOperation,
    allow_folder_delete: bool,
) -> Result<Value> {
    let action = operation.action.as_str();
    let identity = operation.identity.as_str();
    let desired = &operation.desired;
    match action {
        "would-create" => {
            let title = desired
                .get("title")
                .and_then(Value::as_str)
                .map(str::trim)
                .filter(|value| !value.is_empty())
                .unwrap_or(identity);
            let parent_uid = desired
                .get("parentUid")
                .and_then(Value::as_str)
                .map(str::trim)
                .filter(|value| !value.is_empty());
            Ok(Value::Object(
                client
                    .create_folder(title, identity, parent_uid)?
                    .into_iter()
                    .collect(),
            ))
        }
        "would-update" => Ok(Value::Object(
            client
                .update_folder(identity, desired)?
                .into_iter()
                .collect(),
        )),
        "would-delete" => {
            if !allow_folder_delete {
                return Err(message(format!(
                    "Refusing live folder delete for {identity} without --allow-folder-delete."
                )));
            }
            Ok(client.delete_folder(identity)?)
        }
        _ => Err(message(format!("Unsupported folder sync action {action}."))),
    }
}

fn apply_dashboard_operation_with_client(
    client: &SyncLiveClient<'_>,
    operation: &SyncApplyOperation,
) -> Result<Value> {
    let action = operation.action.as_str();
    let identity = operation.identity.as_str();
    if action == "would-delete" {
        return Ok(client.delete_dashboard(identity)?);
    }
    let mut body = operation.desired.clone();
    body.insert("uid".to_string(), Value::String(identity.to_string()));
    let title = body
        .get("title")
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or(identity);
    body.insert("title".to_string(), Value::String(title.to_string()));
    body.remove("id");
    let folder_uid = body
        .get("folderUid")
        .or_else(|| body.get("folderUID"))
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty());
    client.upsert_dashboard(&body, action == "would-update", folder_uid)
}

fn apply_datasource_operation_with_client(
    client: &SyncLiveClient<'_>,
    operation: &SyncApplyOperation,
) -> Result<Value> {
    let action = operation.action.as_str();
    let identity = operation.identity.as_str();
    let mut body = operation.desired.clone();
    if !identity.is_empty() {
        body.entry("uid".to_string())
            .or_insert_with(|| Value::String(identity.to_string()));
    }
    let title = body
        .get("name")
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or(identity);
    body.insert("name".to_string(), Value::String(title.to_string()));
    match action {
        "would-create" => Ok(Value::Object(
            client.create_datasource(&body)?.into_iter().collect(),
        )),
        "would-update" => {
            let target = client.resolve_datasource_target(identity)?.ok_or_else(|| {
                message(format!(
                    "Could not resolve live datasource target {identity} during sync apply."
                ))
            })?;
            let datasource_id = target
                .get("id")
                .map(|value| match value {
                    Value::String(text) => text.clone(),
                    _ => value.to_string(),
                })
                .filter(|value| !value.is_empty())
                .ok_or_else(|| message("Datasource sync update requires a live datasource id."))?;
            Ok(Value::Object(
                client
                    .update_datasource(&datasource_id, &body)?
                    .into_iter()
                    .collect(),
            ))
        }
        "would-delete" => {
            let target = client.resolve_datasource_target(identity)?.ok_or_else(|| {
                message(format!(
                    "Could not resolve live datasource target {identity} during sync apply."
                ))
            })?;
            let datasource_id = target
                .get("id")
                .map(|value| match value {
                    Value::String(text) => text.clone(),
                    _ => value.to_string(),
                })
                .filter(|value| !value.is_empty())
                .ok_or_else(|| message("Datasource sync delete requires a live datasource id."))?;
            Ok(client.delete_datasource(&datasource_id)?)
        }
        _ => Err(message(format!(
            "Unsupported datasource sync action {action}."
        ))),
    }
}

fn apply_alert_operation_with_client(
    client: &SyncLiveClient<'_>,
    operation: &SyncApplyOperation,
) -> Result<Value> {
    let kind = operation.kind.as_str();
    let action = operation.action.as_str();
    let identity = operation.identity.as_str();
    let desired = &operation.desired;
    match action {
        "would-delete" => match kind {
            "alert" => {
                if identity.is_empty() {
                    return Err(message(
                        "Alert sync delete requires a stable uid identity for live apply.",
                    ));
                }
                Ok(client.delete_alert_rule(identity)?)
            }
            "alert-contact-point" => Ok(client.delete_contact_point(identity)?),
            "alert-mute-timing" => Ok(client.delete_mute_timing(identity)?),
            "alert-template" => Ok(client.delete_template(identity)?),
            "alert-policy" => Ok(client.delete_notification_policies()?),
            _ => Err(message(format!("Unsupported alert sync kind {kind}."))),
        },
        "would-create" | "would-update" => match kind {
            "alert" => {
                let mut payload = build_rule_import_payload(desired)?;
                if !identity.is_empty() && !payload.contains_key("uid") {
                    payload.insert("uid".to_string(), Value::String(identity.to_string()));
                }
                let uid = payload
                    .get("uid")
                    .and_then(Value::as_str)
                    .map(str::trim)
                    .filter(|value| !value.is_empty())
                    .ok_or_else(|| {
                        message("Alert sync live apply requires alert rule payloads with a uid.")
                    })?;
                let response = if action == "would-create" {
                    client.create_alert_rule(&payload)?
                } else {
                    client.update_alert_rule(uid, &payload)?
                };
                Ok(Value::Object(response.into_iter().collect()))
            }
            "alert-contact-point" => {
                let mut payload = build_contact_point_import_payload(desired)?;
                if !identity.is_empty() && !payload.contains_key("uid") {
                    payload.insert("uid".to_string(), Value::String(identity.to_string()));
                }
                let response = if action == "would-create" {
                    client.create_contact_point(&payload)?
                } else {
                    client.update_contact_point(identity, &payload)?
                };
                Ok(Value::Object(response.into_iter().collect()))
            }
            "alert-mute-timing" => {
                let payload = build_mute_timing_import_payload(desired)?;
                let name = payload
                    .get("name")
                    .and_then(Value::as_str)
                    .map(str::trim)
                    .filter(|value| !value.is_empty())
                    .unwrap_or(identity);
                let response = if action == "would-create" {
                    client.create_mute_timing(&payload)?
                } else {
                    client.update_mute_timing(name, &payload)?
                };
                Ok(Value::Object(response.into_iter().collect()))
            }
            "alert-policy" => {
                let payload = build_policies_import_payload(desired)?;
                Ok(Value::Object(
                    client
                        .update_notification_policies(&payload)?
                        .into_iter()
                        .collect(),
                ))
            }
            "alert-template" => {
                let mut payload = build_template_import_payload(desired)?;
                let name = payload
                    .get("name")
                    .and_then(Value::as_str)
                    .map(str::trim)
                    .filter(|value| !value.is_empty())
                    .unwrap_or(identity)
                    .to_string();
                payload.remove("name");
                Ok(Value::Object(
                    client
                        .update_template(&name, &payload)?
                        .into_iter()
                        .collect(),
                ))
            }
            _ => Err(message(format!("Unsupported alert sync kind {kind}."))),
        },
        _ => Err(message(format!("Unsupported alert sync action {action}."))),
    }
}

pub(crate) fn execute_live_apply_with_client(
    client: &SyncLiveClient<'_>,
    operations: &[SyncApplyOperation],
    allow_folder_delete: bool,
    allow_policy_reset: bool,
) -> Result<Value> {
    let mut results = Vec::new();
    for operation in operations {
        let kind = operation.kind.as_str();
        let identity = operation.identity.as_str();
        let action = operation.action.as_str();
        let response = match kind {
            "folder" => apply_folder_operation_with_client(client, operation, allow_folder_delete)?,
            "dashboard" => apply_dashboard_operation_with_client(client, operation)?,
            "datasource" => apply_datasource_operation_with_client(client, operation)?,
            "alert"
            | "alert-contact-point"
            | "alert-mute-timing"
            | "alert-policy"
            | "alert-template" => {
                if operation.kind == "alert-policy"
                    && operation.action == "would-delete"
                    && !allow_policy_reset
                {
                    return Err(message(
                        "Refusing live notification policy reset without --allow-policy-reset.",
                    ));
                }
                apply_alert_operation_with_client(client, operation)?
            }
            _ => return Err(message(format!("Unsupported sync resource kind {kind}."))),
        };
        results.push(serde_json::json!({
            "kind": kind,
            "identity": identity,
            "action": action,
            "response": response,
        }));
    }
    Ok(serde_json::json!({
        "mode": "live-apply",
        "appliedCount": results.len(),
        "results": results,
    }))
}

#[cfg(test)]
pub(crate) fn execute_live_apply_with_request<F>(
    request_json: F,
    operations: &[SyncApplyOperation],
    allow_folder_delete: bool,
    allow_policy_reset: bool,
) -> Result<Value>
where
    F: FnMut(reqwest::Method, &str, &[(String, String)], Option<&Value>) -> Result<Option<Value>>,
{
    execute_sync_live_apply_with_request(
        request_json,
        operations,
        allow_folder_delete,
        allow_policy_reset,
    )
}
