//! Unified CLI dispatcher for Rust entrypoints.
//!
//! Purpose:
//! - Own only command topology and domain dispatch.
//! - Keep `grafana-util` command surface in one place.
//! - Route to domain runners without carrying transport logic.

use clap::{Args, Parser, Subcommand};

use crate::access::{
    run_access_cli, AccessCliArgs, AccessCommand, OrgCommand, OrgExportArgs, ServiceAccountCommand,
    ServiceAccountExportArgs, TeamCommand, TeamExportArgs, UserCommand, UserExportArgs,
};
use crate::alert::{
    normalize_alert_group_command, run_alert_cli, AlertAddContactPointArgs, AlertAddRuleArgs,
    AlertApplyArgs, AlertCliArgs, AlertCloneRuleArgs, AlertDeleteArgs, AlertDiffArgs,
    AlertExportArgs, AlertImportArgs, AlertInitArgs, AlertListArgs, AlertNewResourceArgs,
    AlertPlanArgs, AlertPreviewRouteArgs, AlertSetRouteArgs,
};
pub use crate::cli_help::{
    maybe_render_unified_help_from_os_args, render_unified_help_full_text,
    render_unified_help_text, render_unified_version_text,
};
use crate::cli_help::{
    UNIFIED_ACCESS_HELP_TEXT, UNIFIED_ALERT_HELP_TEXT, UNIFIED_DASHBOARD_HELP_TEXT,
    UNIFIED_DATASOURCE_HELP_TEXT, UNIFIED_SYNC_HELP_TEXT,
};
use crate::cli_help_examples::UNIFIED_HELP_TEXT;
use crate::common::{json_color_choice, set_json_color_choice, CliColorChoice, Result};
use crate::dashboard::{
    run_dashboard_cli, AnalyzeArgs, BrowseArgs, CloneLiveArgs, DashboardCliArgs, DashboardCommand,
    DashboardHistoryArgs, DeleteArgs, DiffArgs, EditLiveArgs, ExportArgs as DashboardExportArgs,
    GetArgs, GovernanceGateArgs, ImpactArgs, ImportArgs, InspectVarsArgs, ListArgs, PatchFileArgs,
    PublishArgs, RawToPromptArgs, ReviewArgs, ScreenshotArgs, ServeArgs, TopologyArgs,
};
use crate::datasource::{run_datasource_cli, DatasourceExportArgs, DatasourceGroupCommand};
use crate::migrate::{run_migrate_cli, MigrateCliArgs, MigrateCommand, MigrateDashboardCommand};
use crate::overview::{run_overview_cli, OverviewArgs, OverviewCliArgs, OverviewCommand};
use crate::profile_cli::{run_profile_cli, ProfileCliArgs};
use crate::project_status_command::{
    run_project_status_cli, ProjectStatusCliArgs, ProjectStatusLiveArgs, ProjectStatusStagedArgs,
    ProjectStatusSubcommand,
};
use crate::resource::{run_resource_cli, ResourceCliArgs, ResourceCommand};
use crate::snapshot::{run_snapshot_cli, SnapshotCommand};
use crate::sync::{run_sync_cli, SyncGroupCommand};

#[derive(Debug, Clone, Subcommand)]
pub enum ObserveCommand {
    #[command(about = "Render shared project-wide live status.")]
    Live(ProjectStatusLiveArgs),
    #[command(about = "Render shared project-wide staged status.")]
    Staged(ProjectStatusStagedArgs),
    #[command(about = "Render project-wide staged or live overview.")]
    Overview {
        #[command(flatten)]
        staged: OverviewArgs,
        #[command(subcommand)]
        command: Option<OverviewCommand>,
    },
    #[command(about = "Export or review live dashboard snapshots.")]
    Snapshot {
        #[command(subcommand)]
        command: SnapshotCommand,
    },
    #[command(about = "Run generic read-only Grafana resource queries.")]
    Resource {
        #[command(subcommand)]
        command: ResourceCommand,
    },
}

#[derive(Debug, Clone, Subcommand)]
pub enum ConfigCommand {
    #[command(about = "Manage repo-local Grafana connection profiles.")]
    Profile(ProfileCliArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum ExportAccessCommand {
    #[command(about = "Export Grafana users into a local reviewable bundle.")]
    User(UserExportArgs),
    #[command(about = "Export Grafana org inventory into a local reviewable bundle.")]
    Org(OrgExportArgs),
    #[command(about = "Export Grafana teams into a local reviewable bundle.")]
    Team(TeamExportArgs),
    #[command(
        name = "service-account",
        about = "Export Grafana service accounts into a local reviewable bundle."
    )]
    ServiceAccount(ServiceAccountExportArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum ExportCommand {
    #[command(about = "Export dashboards into a local artifact tree for review or backup.")]
    Dashboard(DashboardExportArgs),
    #[command(
        about = "Export alerting resources into a local artifact tree for review or backup."
    )]
    Alert(AlertExportArgs),
    #[command(
        about = "Export datasource inventory into a local artifact tree for review or backup."
    )]
    Datasource(DatasourceExportArgs),
    #[command(about = "Export access inventory into a local artifact tree for review or backup.")]
    Access {
        #[command(subcommand)]
        command: ExportAccessCommand,
    },
}

#[derive(Debug, Clone, Subcommand)]
pub enum DashboardLiveCommand {
    #[command(about = "Browse the live dashboard tree in an interactive terminal UI.")]
    Browse(BrowseArgs),
    #[command(
        name = "list",
        about = "List dashboard summaries without writing export files."
    )]
    List(ListArgs),
    #[command(
        name = "vars",
        about = "List dashboard templating variables from live Grafana or local artifacts."
    )]
    Vars(InspectVarsArgs),
    #[command(
        name = "fetch",
        about = "Fetch one live dashboard into an API-safe local JSON draft."
    )]
    Fetch(GetArgs),
    #[command(
        name = "clone",
        about = "Clone one live dashboard into a local draft with optional overrides."
    )]
    Clone(CloneLiveArgs),
    #[command(
        name = "edit",
        about = "Edit one live dashboard through an external editor."
    )]
    Edit(EditLiveArgs),
    #[command(
        name = "delete",
        about = "Delete live dashboards by UID or folder path."
    )]
    Delete(DeleteArgs),
    #[command(
        name = "history",
        about = "List, restore, diff, or export live dashboard revision history."
    )]
    History(DashboardHistoryArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum DashboardDraftCommand {
    #[command(
        name = "review",
        about = "Review one local dashboard JSON file without touching Grafana."
    )]
    Review(ReviewArgs),
    #[command(
        name = "patch",
        about = "Patch one local dashboard JSON file in place or to a new path."
    )]
    Patch(PatchFileArgs),
    #[command(
        name = "serve",
        about = "Serve dashboard drafts through a local preview server."
    )]
    Serve(ServeArgs),
    #[command(
        name = "publish",
        about = "Publish one local dashboard JSON file through the existing dashboard import pipeline."
    )]
    Publish(PublishArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum DashboardSyncConvertCommand {
    #[command(
        name = "raw-to-prompt",
        about = "Convert raw dashboard exports into prompt lane artifacts."
    )]
    RawToPrompt(RawToPromptArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum DashboardSyncCommand {
    #[command(
        name = "export",
        about = "Export dashboards to raw/ and prompt/ JSON files."
    )]
    Export(DashboardExportArgs),
    #[command(
        name = "import",
        about = "Import dashboard JSON files through the Grafana API."
    )]
    Import(ImportArgs),
    #[command(
        name = "diff",
        about = "Compare local raw dashboard files against live Grafana dashboards."
    )]
    Diff(DiffArgs),
    #[command(name = "convert", about = "Run dashboard format conversion workflows.")]
    Convert {
        #[command(subcommand)]
        command: DashboardSyncConvertCommand,
    },
}

#[derive(Debug, Clone, Subcommand)]
pub enum DashboardAnalyzeCommand {
    #[command(
        name = "summary",
        about = "Analyze dashboards from live Grafana or a local export tree."
    )]
    Summary(AnalyzeArgs),
    #[command(
        name = "topology",
        about = "Show which dashboards, variables, data sources, and alerts depend on each other."
    )]
    Topology(TopologyArgs),
    #[command(
        name = "impact",
        about = "Show which dashboards and alert resources would be affected by one data source."
    )]
    Impact(ImpactArgs),
    #[command(
        name = "governance",
        about = "Evaluate governance policy against dashboard inspect JSON artifacts."
    )]
    Governance(GovernanceGateArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum DashboardCaptureCommand {
    #[command(
        name = "screenshot",
        about = "Open one dashboard in a headless browser and capture image or PDF output."
    )]
    Screenshot(ScreenshotArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum DashboardGroupCommand {
    #[command(about = "Work with live dashboards and history.")]
    Live {
        #[command(subcommand)]
        command: DashboardLiveCommand,
    },
    #[command(about = "Work with local dashboard drafts before publish.")]
    Draft {
        #[command(subcommand)]
        command: DashboardDraftCommand,
    },
    #[command(about = "Move dashboards between local artifacts and Grafana.")]
    Sync {
        #[command(subcommand)]
        command: DashboardSyncCommand,
    },
    #[command(about = "Analyze dashboard structure, dependencies, and governance.")]
    Analyze {
        #[command(subcommand)]
        command: DashboardAnalyzeCommand,
    },
    #[command(about = "Capture browser-rendered dashboard artifacts.")]
    Capture {
        #[command(subcommand)]
        command: DashboardCaptureCommand,
    },
}

#[derive(Debug, Clone, Subcommand)]
pub enum AlertLiveCommand {
    #[command(name = "list-rules", about = "List live Grafana alert rules.")]
    ListRules(AlertListArgs),
    #[command(
        name = "list-contact-points",
        about = "List live Grafana alert contact points."
    )]
    ListContactPoints(AlertListArgs),
    #[command(name = "list-mute-timings", about = "List live Grafana mute timings.")]
    ListMuteTimings(AlertListArgs),
    #[command(
        name = "list-templates",
        about = "List live Grafana notification templates."
    )]
    ListTemplates(AlertListArgs),
    #[command(
        name = "delete",
        about = "Delete one explicit alert resource identity."
    )]
    Delete(AlertDeleteArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum AlertMigrateCommand {
    #[command(
        name = "export",
        about = "Export alerting resources into raw/ JSON files."
    )]
    Export(AlertExportArgs),
    #[command(
        name = "import",
        about = "Import alerting resource JSON files through the Grafana API."
    )]
    Import(AlertImportArgs),
    #[command(
        name = "diff",
        about = "Compare local alerting export files against live Grafana resources."
    )]
    Diff(AlertDiffArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum AlertAuthorRuleCommand {
    #[command(
        name = "add",
        about = "Add a managed alert rule into the staged desired tree."
    )]
    Add(AlertAddRuleArgs),
    #[command(
        name = "clone",
        about = "Clone an existing staged alert rule into a new authoring target."
    )]
    Clone(AlertCloneRuleArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum AlertAuthorContactPointCommand {
    #[command(
        name = "add",
        about = "Add a managed contact point into the staged desired tree."
    )]
    Add(AlertAddContactPointArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum AlertAuthorRouteCommand {
    #[command(
        name = "set",
        about = "Set the tool-owned managed route inside the desired tree."
    )]
    Set(AlertSetRouteArgs),
    #[command(
        name = "preview",
        about = "Preview how the staged managed route would match labels and severity."
    )]
    Preview(AlertPreviewRouteArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum AlertAuthorCommand {
    #[command(name = "init", about = "Initialize a staged desired-state alert tree.")]
    Init(AlertInitArgs),
    #[command(name = "rule", about = "Author or clone managed alert rules.")]
    Rule {
        #[command(subcommand)]
        command: AlertAuthorRuleCommand,
    },
    #[command(name = "contact-point", about = "Author managed alert contact points.")]
    ContactPoint {
        #[command(subcommand)]
        command: AlertAuthorContactPointCommand,
    },
    #[command(
        name = "route",
        about = "Author or preview the managed alert routing subtree."
    )]
    Route {
        #[command(subcommand)]
        command: AlertAuthorRouteCommand,
    },
}

#[derive(Debug, Clone, Subcommand)]
pub enum AlertScaffoldCommand {
    #[command(
        name = "rule",
        about = "Seed a low-level rule scaffold into the desired tree."
    )]
    Rule(AlertNewResourceArgs),
    #[command(
        name = "contact-point",
        about = "Seed a low-level contact-point scaffold into the desired tree."
    )]
    ContactPoint(AlertNewResourceArgs),
    #[command(
        name = "template",
        about = "Seed a low-level template scaffold into the desired tree."
    )]
    Template(AlertNewResourceArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum AlertChangeCommand {
    #[command(
        name = "plan",
        about = "Build a staged alert change plan from desired files."
    )]
    Plan(AlertPlanArgs),
    #[command(
        name = "apply",
        about = "Apply a reviewed alert plan after explicit approval."
    )]
    Apply(AlertApplyArgs),
}

#[derive(Debug, Clone, Args)]
pub struct AlertSurfaceArgs {
    #[command(subcommand)]
    pub command: AlertCommandSurface,
}

#[derive(Debug, Clone, Subcommand)]
pub enum AlertCommandSurface {
    #[command(about = "Read live alert inventory or delete one live alert resource.")]
    Live {
        #[command(subcommand)]
        command: AlertLiveCommand,
    },
    #[command(about = "Move alert resources between local artifacts and Grafana.")]
    Migrate {
        #[command(subcommand)]
        command: AlertMigrateCommand,
    },
    #[command(about = "Author managed alert desired-state resources.")]
    Author {
        #[command(subcommand)]
        command: AlertAuthorCommand,
    },
    #[command(about = "Seed low-level alert resource scaffolds.")]
    Scaffold {
        #[command(subcommand)]
        command: AlertScaffoldCommand,
    },
    #[command(about = "Plan or apply staged alert changes.")]
    Change {
        #[command(subcommand)]
        command: AlertChangeCommand,
    },
}

#[derive(Debug, Clone, Subcommand)]
pub enum AdvancedCommand {
    #[command(
        about = "Run full dashboard browse, authoring, import, analysis, and capture workflows."
    )]
    Dashboard {
        #[command(subcommand)]
        command: DashboardGroupCommand,
    },
    #[command(about = "Run grouped alert inventory, migration, authoring, and change workflows.")]
    Alert(AlertSurfaceArgs),
    #[command(about = "Run datasource list, browse, export, import, and diff workflows.")]
    Datasource {
        #[arg(
            long,
            global = true,
            value_enum,
            help = "Override JSON/YAML/table color for the datasource namespace."
        )]
        color: Option<CliColorChoice>,
        #[command(subcommand)]
        command: DatasourceGroupCommand,
    },
    #[command(about = "List and manage Grafana users, teams, and service accounts.")]
    Access(AccessCliArgs),
}

#[derive(Debug, Clone, Subcommand)]
pub enum UnifiedCommand {
    #[command(about = "Print the current grafana-util version.")]
    Version(VersionArgs),
    #[command(about = "Read live and staged Grafana state through a shared observe surface.")]
    Observe {
        #[command(subcommand)]
        command: ObserveCommand,
    },
    #[command(
        about = "Run common export and backup flows without learning domain-heavy subtrees."
    )]
    Export {
        #[command(subcommand)]
        command: ExportCommand,
    },
    #[command(
        about = "Open expert and domain-specific workflows once you know which subsystem you need."
    )]
    Advanced {
        #[command(subcommand)]
        command: AdvancedCommand,
    },
    #[command(
        hide = true,
        about = "Compatibility path for full dashboard browse, authoring, export, import, analysis, and capture workflows.",
        visible_alias = "db",
        after_help = UNIFIED_DASHBOARD_HELP_TEXT
    )]
    Dashboard {
        #[command(subcommand)]
        command: DashboardGroupCommand,
    },
    #[command(
        hide = true,
        about = "Compatibility path for datasource list, browse, export, import, and diff workflows.",
        visible_alias = "ds",
        after_help = UNIFIED_DATASOURCE_HELP_TEXT
    )]
    Datasource {
        #[arg(
            long,
            global = true,
            value_enum,
            help = "Override JSON/YAML/table color for the datasource namespace."
        )]
        color: Option<CliColorChoice>,
        #[command(subcommand)]
        command: DatasourceGroupCommand,
    },
    #[command(
        hide = true,
        about = "Compatibility path for grouped alert inventory, migration, authoring, and change workflows.",
        after_help = UNIFIED_ALERT_HELP_TEXT
    )]
    Alert(AlertSurfaceArgs),
    #[command(
        hide = true,
        about = "Compatibility path for Grafana users, teams, and service accounts.",
        after_help = UNIFIED_ACCESS_HELP_TEXT
    )]
    Access(AccessCliArgs),
    #[command(
        name = "change",
        about = "Run review-first change workflows with optional live Grafana fetch/apply paths.",
        after_help = UNIFIED_SYNC_HELP_TEXT
    )]
    Change {
        #[command(subcommand)]
        command: SyncGroupCommand,
    },
    #[command(about = "Run repo-local Grafana configuration and profile workflows.")]
    Config {
        #[command(subcommand)]
        command: ConfigCommand,
    },
    #[command(
        hide = true,
        about = "Compatibility path for migration and artifact repair workflows."
    )]
    Migrate {
        #[command(subcommand)]
        command: MigrateCommand,
    },
}

#[derive(Debug, Clone, Args)]
pub struct VersionArgs {
    #[arg(long, help = "Render version details as JSON for external tooling.")]
    pub json: bool,
}

#[derive(Debug, Clone, Parser)]
#[command(
    name = "grafana-util",
    version = crate::common::TOOL_VERSION_DETAILS,
    about = "Task-first Grafana CLI for observe, export, change review, config, and advanced workflows.",
    after_help = UNIFIED_HELP_TEXT,
    styles = crate::help_styles::CLI_HELP_STYLES
)]
pub struct CliArgs {
    #[arg(
        long,
        value_enum,
        default_value_t = CliColorChoice::Auto,
        help = "Colorize JSON output. Use auto, always, or never."
    )]
    pub color: CliColorChoice,
    #[command(subcommand)]
    pub command: UnifiedCommand,
}

pub fn parse_cli_from<I, T>(iter: I) -> CliArgs
where
    I: IntoIterator<Item = T>,
    T: Into<std::ffi::OsString> + Clone,
{
    CliArgs::parse_from(iter)
}

fn wrap_dashboard(command: DashboardCommand) -> DashboardCliArgs {
    DashboardCliArgs {
        color: json_color_choice(),
        command,
    }
}

fn wrap_dashboard_group(command: DashboardGroupCommand) -> DashboardCliArgs {
    match command {
        DashboardGroupCommand::Live { command } => match command {
            DashboardLiveCommand::Browse(inner) => wrap_dashboard(DashboardCommand::Browse(inner)),
            DashboardLiveCommand::List(inner) => wrap_dashboard(DashboardCommand::List(inner)),
            DashboardLiveCommand::Vars(inner) => {
                wrap_dashboard(DashboardCommand::InspectVars(inner))
            }
            DashboardLiveCommand::Fetch(inner) => wrap_dashboard(DashboardCommand::Get(inner)),
            DashboardLiveCommand::Clone(inner) => {
                wrap_dashboard(DashboardCommand::CloneLive(inner))
            }
            DashboardLiveCommand::Edit(inner) => wrap_dashboard(DashboardCommand::EditLive(inner)),
            DashboardLiveCommand::Delete(inner) => wrap_dashboard(DashboardCommand::Delete(inner)),
            DashboardLiveCommand::History(inner) => {
                wrap_dashboard(DashboardCommand::History(inner))
            }
        },
        DashboardGroupCommand::Draft { command } => match command {
            DashboardDraftCommand::Review(inner) => wrap_dashboard(DashboardCommand::Review(inner)),
            DashboardDraftCommand::Patch(inner) => {
                wrap_dashboard(DashboardCommand::PatchFile(inner))
            }
            DashboardDraftCommand::Serve(inner) => wrap_dashboard(DashboardCommand::Serve(inner)),
            DashboardDraftCommand::Publish(inner) => {
                wrap_dashboard(DashboardCommand::Publish(inner))
            }
        },
        DashboardGroupCommand::Sync { command } => match command {
            DashboardSyncCommand::Export(inner) => wrap_dashboard(DashboardCommand::Export(inner)),
            DashboardSyncCommand::Import(inner) => wrap_dashboard(DashboardCommand::Import(inner)),
            DashboardSyncCommand::Diff(inner) => wrap_dashboard(DashboardCommand::Diff(inner)),
            DashboardSyncCommand::Convert { .. } => {
                unreachable!("convert is handled before dashboard dispatch")
            }
        },
        DashboardGroupCommand::Analyze { command } => match command {
            DashboardAnalyzeCommand::Summary(inner) => {
                wrap_dashboard(DashboardCommand::Analyze(inner))
            }
            DashboardAnalyzeCommand::Topology(inner) => {
                wrap_dashboard(DashboardCommand::Topology(inner))
            }
            DashboardAnalyzeCommand::Impact(inner) => {
                wrap_dashboard(DashboardCommand::Impact(inner))
            }
            DashboardAnalyzeCommand::Governance(inner) => {
                wrap_dashboard(DashboardCommand::GovernanceGate(inner))
            }
        },
        DashboardGroupCommand::Capture { command } => match command {
            DashboardCaptureCommand::Screenshot(inner) => {
                wrap_dashboard(DashboardCommand::Screenshot(inner))
            }
        },
    }
}

fn wrap_alert_surface(command: AlertCommandSurface) -> AlertCliArgs {
    use crate::alert::AlertGroupCommand;

    let legacy = match command {
        AlertCommandSurface::Live { command } => match command {
            AlertLiveCommand::ListRules(inner) => AlertGroupCommand::ListRules(inner),
            AlertLiveCommand::ListContactPoints(inner) => {
                AlertGroupCommand::ListContactPoints(inner)
            }
            AlertLiveCommand::ListMuteTimings(inner) => AlertGroupCommand::ListMuteTimings(inner),
            AlertLiveCommand::ListTemplates(inner) => AlertGroupCommand::ListTemplates(inner),
            AlertLiveCommand::Delete(inner) => AlertGroupCommand::Delete(inner),
        },
        AlertCommandSurface::Migrate { command } => match command {
            AlertMigrateCommand::Export(inner) => AlertGroupCommand::Export(inner),
            AlertMigrateCommand::Import(inner) => AlertGroupCommand::Import(inner),
            AlertMigrateCommand::Diff(inner) => AlertGroupCommand::Diff(inner),
        },
        AlertCommandSurface::Author { command } => match command {
            AlertAuthorCommand::Init(inner) => AlertGroupCommand::Init(inner),
            AlertAuthorCommand::Rule { command } => match command {
                AlertAuthorRuleCommand::Add(inner) => AlertGroupCommand::AddRule(inner),
                AlertAuthorRuleCommand::Clone(inner) => AlertGroupCommand::CloneRule(inner),
            },
            AlertAuthorCommand::ContactPoint { command } => match command {
                AlertAuthorContactPointCommand::Add(inner) => {
                    AlertGroupCommand::AddContactPoint(inner)
                }
            },
            AlertAuthorCommand::Route { command } => match command {
                AlertAuthorRouteCommand::Set(inner) => AlertGroupCommand::SetRoute(inner),
                AlertAuthorRouteCommand::Preview(inner) => AlertGroupCommand::PreviewRoute(inner),
            },
        },
        AlertCommandSurface::Scaffold { command } => match command {
            AlertScaffoldCommand::Rule(inner) => AlertGroupCommand::NewRule(inner),
            AlertScaffoldCommand::ContactPoint(inner) => AlertGroupCommand::NewContactPoint(inner),
            AlertScaffoldCommand::Template(inner) => AlertGroupCommand::NewTemplate(inner),
        },
        AlertCommandSurface::Change { command } => match command {
            AlertChangeCommand::Plan(inner) => AlertGroupCommand::Plan(inner),
            AlertChangeCommand::Apply(inner) => AlertGroupCommand::Apply(inner),
        },
    };

    normalize_alert_group_command(legacy)
}

fn wrap_overview(staged: OverviewArgs, command: Option<OverviewCommand>) -> OverviewCliArgs {
    OverviewCliArgs {
        color: json_color_choice(),
        staged,
        command,
    }
}

fn run_dashboard_sync_convert(args: RawToPromptArgs) -> Result<()> {
    run_migrate_cli(MigrateCliArgs {
        command: MigrateCommand::Dashboard {
            command: MigrateDashboardCommand::RawToPrompt(args),
        },
    })
}

fn wrap_export_access(command: ExportAccessCommand) -> AccessCliArgs {
    let command = match command {
        ExportAccessCommand::User(inner) => AccessCommand::User {
            command: UserCommand::Export(inner),
        },
        ExportAccessCommand::Org(inner) => AccessCommand::Org {
            command: OrgCommand::Export(inner),
        },
        ExportAccessCommand::Team(inner) => AccessCommand::Team {
            command: TeamCommand::Export(inner),
        },
        ExportAccessCommand::ServiceAccount(inner) => AccessCommand::ServiceAccount {
            command: ServiceAccountCommand::Export(inner),
        },
    };
    AccessCliArgs { command }
}

fn wrap_project_status(command: ObserveCommand) -> Option<ProjectStatusCliArgs> {
    match command {
        ObserveCommand::Live(inner) => Some(ProjectStatusCliArgs {
            color: json_color_choice(),
            command: ProjectStatusSubcommand::Live(inner),
        }),
        ObserveCommand::Staged(inner) => Some(ProjectStatusCliArgs {
            color: json_color_choice(),
            command: ProjectStatusSubcommand::Staged(inner),
        }),
        _ => None,
    }
}

#[allow(clippy::too_many_arguments)]
fn dispatch_with_handlers<FD, FS, FY, FA, FX, FP, FR, FO, FQ>(
    args: CliArgs,
    mut run_dashboard: FD,
    mut run_datasource: FS,
    mut run_sync: FY,
    mut run_alert: FA,
    mut run_access: FX,
    mut run_profile: FP,
    mut run_snapshot: FR,
    mut run_overview: FO,
    mut run_project_status: FQ,
) -> Result<()>
where
    FD: FnMut(DashboardCliArgs) -> Result<()>,
    FS: FnMut(DatasourceGroupCommand) -> Result<()>,
    FY: FnMut(SyncGroupCommand) -> Result<()>,
    FA: FnMut(AlertCliArgs) -> Result<()>,
    FX: FnMut(AccessCliArgs) -> Result<()>,
    FP: FnMut(ProfileCliArgs) -> Result<()>,
    FR: FnMut(SnapshotCommand) -> Result<()>,
    FO: FnMut(OverviewCliArgs) -> Result<()>,
    FQ: FnMut(ProjectStatusCliArgs) -> Result<()>,
{
    let default_color = args.color;
    match args.command {
        UnifiedCommand::Version(args) => {
            if args.json {
                let payload = serde_json::json!({
                    "schemaVersion": crate::common::TOOL_VERSION_SCHEMA_VERSION,
                    "name": "grafana-util",
                    "version": crate::common::tool_version(),
                    "commit": crate::common::tool_git_commit(),
                    "buildTime": crate::common::tool_build_time(),
                });
                print!(
                    "{}",
                    crate::common::render_json_value_with_choice(&payload, default_color, false)?
                );
            } else {
                print!("{}", render_unified_version_text());
            }
            Ok(())
        }
        UnifiedCommand::Observe { command } => match command {
            ObserveCommand::Overview { staged, command } => {
                run_overview(wrap_overview(staged, command))
            }
            ObserveCommand::Snapshot { command } => run_snapshot(command),
            ObserveCommand::Resource { command } => run_resource_cli(ResourceCliArgs {
                color: json_color_choice(),
                command,
            }),
            other => run_project_status(wrap_project_status(other).expect("observe status path")),
        },
        UnifiedCommand::Export { command } => match command {
            ExportCommand::Dashboard(inner) => {
                run_dashboard(wrap_dashboard(DashboardCommand::Export(inner)))
            }
            ExportCommand::Alert(inner) => {
                run_alert(wrap_alert_surface(AlertCommandSurface::Migrate {
                    command: AlertMigrateCommand::Export(inner),
                }))
            }
            ExportCommand::Datasource(inner) => {
                run_datasource(DatasourceGroupCommand::Export(inner))
            }
            ExportCommand::Access { command } => run_access(wrap_export_access(command)),
        },
        UnifiedCommand::Advanced { command } => match command {
            AdvancedCommand::Dashboard { command } => match command {
                DashboardGroupCommand::Sync {
                    command:
                        DashboardSyncCommand::Convert {
                            command: DashboardSyncConvertCommand::RawToPrompt(inner),
                        },
                } => run_dashboard_sync_convert(inner),
                other => run_dashboard(wrap_dashboard_group(other)),
            },
            AdvancedCommand::Alert(inner) => run_alert(wrap_alert_surface(inner.command)),
            AdvancedCommand::Datasource { color, command } => {
                set_json_color_choice(color.unwrap_or(default_color));
                run_datasource(command)
            }
            AdvancedCommand::Access(inner) => run_access(inner),
        },
        UnifiedCommand::Dashboard { command } => match command {
            DashboardGroupCommand::Sync {
                command:
                    DashboardSyncCommand::Convert {
                        command: DashboardSyncConvertCommand::RawToPrompt(inner),
                    },
            } => run_dashboard_sync_convert(inner),
            other => run_dashboard(wrap_dashboard_group(other)),
        },
        UnifiedCommand::Datasource { color, command } => {
            set_json_color_choice(color.unwrap_or(default_color));
            run_datasource(command)
        }
        UnifiedCommand::Alert(inner) => run_alert(wrap_alert_surface(inner.command)),
        UnifiedCommand::Access(inner) => run_access(inner),
        UnifiedCommand::Change { command } => run_sync(command),
        UnifiedCommand::Config { command } => match command {
            ConfigCommand::Profile(inner) => run_profile(inner),
        },
        UnifiedCommand::Migrate { command } => run_migrate_cli(MigrateCliArgs { command }),
    }
}

pub fn run_cli(args: CliArgs) -> Result<()> {
    set_json_color_choice(args.color);
    dispatch_with_handlers(
        args,
        run_dashboard_cli,
        run_datasource_cli,
        run_sync_cli,
        run_alert_cli,
        run_access_cli,
        run_profile_cli,
        run_snapshot_cli,
        run_overview_cli,
        run_project_status_cli,
    )
}

#[cfg(test)]
#[path = "cli_rust_tests.rs"]
mod cli_rust_tests;
