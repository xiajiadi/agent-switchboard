import { App, applyDocumentTheme, applyHostFonts, applyHostStyleVariables } from "@modelcontextprotocol/ext-apps";

const app = new App({ name: "Agent Switchboard", version: "0.1.0" }, {}, { autoResize: true });
const state = {
  scope: "project",
  target: "subagents",
  catalog: [],
  config: null,
  projectRoot: "",
  language: "zh",
  pendingModel: undefined,
  pendingReasoning: undefined,
  statusKey: null,
  statusValues: {},
  statusKind: "",
  compactManuallyEdited: false,
  pendingReview: null,
  connected: false,
  configReady: false,
  configFailed: false,
  configLoadSequence: 0,
  pendingRoleDelete: null,
};

const COPY = {
  zh: {
    tokenRangeError: "请输入 {min} 到 {max} 之间的整数。",
    subtitle: "管理 Codex 模型与 Agent 配置", scopeTabs: "配置作用域", project: "当前项目", global: "全局",
    scopeTitle: "作用范围", globalDescription: "保存到用户级 config.toml", projectDescription: "保存到项目 .codex/config.toml",
    agentType: "Agent 类型", mainAgent: "主 Agent", defaultSubagents: "默认子 Agent",
    namedRole: "命名角色", roleName: "角色名称", rolePlaceholder: "例如 reviewer", roleHelp: "使用小写字母开头，可包含数字、连字符和下划线。",
    stepUpContext: "增加上下文窗口", stepDownContext: "减少上下文窗口", stepUpCompact: "增加自动压缩阈值", stepDownCompact: "减少自动压缩阈值",
    projectFolder: "项目文件夹", projectPlaceholder: "输入项目的绝对路径",
    projectNeedPath: "请填入当前项目的绝对路径，再读取或写入项目配置。", globalScopeNote: "全局设置作为所有项目的默认值。",
    profileScopeNote: "当前使用 profile {profile}，它可能覆盖此文件中的部分值。",
    modelSection: "模型与推理", catalogNote: "来自本机 Codex 模型目录", model: "模型", reasoning: "推理强度", speed: "速度",
    unchanged: "不修改此层", currentModel: "不修改（当前模型：{value}）", noModelChoice: "选择模型", reasoningNoChangeCurrent: "不修改（当前有效：{value}）", speedNoChange: "不修改此层",
    speedStandard: "标准", speedFast: "快速",
    contextSection: "上下文与自动压缩", contextWindow: "上下文窗口", compactLimit: "自动压缩阈值",
    inheritDefault: "继承 Codex 默认值",
    resultTitle: "更改预览", preparing: "准备应用", saved: "配置已保存",
    reset: "清除此层覆盖", refresh: "刷新模型目录", preview: "预览更改", apply: "应用设置",
    footnote: "设置直接写入 Codex 官方 TOML 配置；本插件不保存另一份模型或项目设置。",
    loadingSettings: "正在读取配置…", loaded: "已读取 Codex 模型目录和配置。", loadingConfig: "正在读取配置…", configReady: "配置已读取，模型目录继续加载",
    projectLoaded: "已读取项目配置。", checking: "正在检查设置…", validating: "正在验证设置…", previewUpdated: "预览已更新。",
    catalogRefreshing: "正在刷新模型目录…", catalogRefreshed: "模型目录已刷新。", fallbackCatalog: "本机 Codex 模型目录不可用，当前显示内置的保守模型列表。",
    commandCopied: "启动命令已复制。", commandSelected: "命令已选中，请复制。", commandGenerated: "命令已生成；当前对话没有改变。",
    savedConfig: "已更新 Codex TOML 配置。",
    overrideCleared: "本层覆盖已清除", layerCleared: "已清除此层覆盖。",
    reasoningUnknown: "当前模型不在可选目录中，无法确认它支持的推理档位。", reasoningNoLevels: "该模型目录没有提供可选推理档位。",
    reasoningUnsupported: "当前推理强度 {value} 不受所选模型支持，请选择一个可用档位。", reasoningHelp: "可选档位按所选模型的 Codex 能力目录显示。",
    reasoningChanged: "所选模型不支持当前推理强度，已改为该模型的默认档位；应用前可调整。",
    reasoningAdjusted: "当前值「{current}」不受所选模型支持；已暂选「{selected}」，点击应用后才会写入。",
    effort_none: "无", effort_low: "低", effort_medium: "中", effort_high: "高", effort_xhigh: "极高", effort_max: "最高", effort_ultra: "极限",
    operationFailed: "操作失败。",
    mainAgentPickerNote: "主 Agent 的模型、推理强度和速度请在聊天框右下角的模型选择器中调整。",
    projectTrustWarning: "Codex 只会加载受信任项目的项目级配置。请确认项目已受信任后再依赖这些设置。",
    currentProjectLabel: "当前项目", globalLabel: "全局", roleTarget: "命名角色：{name}",
    scopeMeta: "配置作用域", agentMeta: "Agent 类型", fileMeta: "写入文件",
    reviewApply: "预览并应用", reviewTitle: "确认配置更改", reviewSubtitle: "核对修改范围和字段值；确认后才会写入配置。",
    reviewResetSubtitle: "此操作会移除当前层中 Agent Switchboard 管理的覆盖值。", resetReviewTitle: "确认清除此层覆盖",
    reviewErrorTitle: "无法生成预览", setting: "设置项", before: "更改前", after: "更改后",
    backToEdit: "返回修改", confirmApply: "确认并应用", confirmReset: "确认清除此层覆盖",
    close: "关闭", noChanges: "当前层没有可清除的覆盖值。", inheritValue: "继承上层或 Codex 默认值",
    reviewNoChanges: "当前设置没有产生字段变化。可以返回继续调整，或关闭此窗口。",
    projectChanged: "已读取所选项目配置。", trustWarningTitle: "项目受信任状态",
    setting_model: "模型", setting_reasoning: "推理强度", setting_speed: "速度",
    setting_context: "上下文窗口", setting_compact: "自动压缩阈值",
    helpTitle: "Agent Switchboard 使用说明",
    helpProject: "当前项目：设置保存在项目目录的 .codex/config.toml。Codex 只读取受信任项目的配置。",
    helpGlobal: "全局：设置保存在用户目录的 config.toml，作为所有项目的默认值。项目配置或命令行参数可覆盖它；清除覆盖后会恢复继承。",
    helpAgents: "默认子 Agent 使用此处选择的模型和推理强度；命名角色可单独设置，也可查看、编辑和删除项目及全局角色。主 Agent 的模型、推理强度和速度在聊天框右下角调整。",
    helpModel: "模型列表来自本机 Codex 模型目录，推理档位随所选模型变化。标准会清除此配置层的快速模式；其他配置层仍可能启用快速模式。",
    helpContext: "空白表示继承，框内数字为当前值。上下文范围为 256,000 至所选模型上限；步长为 10,000，临近边界时自动对齐。范围外的数字不能应用。修改上下文会按 Codex 建议更新压缩阈值，也可手动调整。",
    helpTiming: "模型、推理强度和速度供后续请求读取；上下文和压缩阈值在新 Agent 启动时读取。上下文、压缩阈值和速度属于配置层共享设置，可能影响继承该层的其他 Agent。",
    helpReview: "选择“预览并应用”后，核对写入位置、Agent 类型、修改前后值和提醒；确认后才会写入配置。操作日志可展开查看写入路径和值。",
    gotIt: "知道了", profileWarning: "当前 profile {profile} 的优先级较高，可能覆盖此处设置。",
    sharedSettingWarning: "上下文、自动压缩和速度属于配置层级的共享设置，可能影响继承此层配置的主 Agent 和其他 Agent。",
    clearFastWarning: "移除当前层的快速模式后，较低优先级的配置仍可能启用快速模式。",
    manageRoles: "查看已有角色", rolesTitle: "已有角色", projectRoles: "项目角色", globalRoles: "全局角色",
    rolesLoading: "正在读取角色…", rolesEmpty: "还没有命名角色", rolesNeedProject: "填写项目文件夹后可查看项目角色",
    editRole: "编辑", deleteRole: "删除", deleteRoleTitle: "删除命名角色", cancel: "取消",
    deleteRolePrompt: "确定删除“{name}”的{scope}配置吗？",
    deleteRoleWarning: "将移除此作用域中的角色定义。默认角色配置文件会同时删除；自定义或被其他角色共用的文件会保留。",
    deleteRoleFiles: "涉及文件",
    roleDeleted: "已删除角色“{name}”", roleReloadFailed: "角色已删除，但列表刷新失败。", roleNoSettings: "未设置专属参数，使用继承值",
    roleDeleteCustomKept: "角色已删除，自定义配置文件已保留。", roleDeleteSharedKept: "角色已删除，共用配置文件已保留。",
    roleDeleteFileFailed: "角色已删除，但默认配置文件无法删除。",
    openLogs: "操作日志", logsTitle: "操作日志",
    refreshLogs: "刷新日志", logsLoading: "正在读取日志…", logsEmpty: "暂无操作记录", logsFailed: "无法读取插件日志。",
    logResult_success: "成功", logResult_error: "失败", logDuration: "耗时 {value} 毫秒", logDetails: "查看详情",
    logRoleName: "角色", logFilesWritten: "写入文件", logFilesDeleted: "删除文件", logPreservedFile: "保留文件",
    logOrphanedFile: "遗留角色文件", logSettingsWritten: "写入配置", logSettingsBefore: "修改前配置", logSettingsRemoved: "移除配置", logChangedSettings: "变更字段",
    logScope_project: "项目", logScope_global: "全局",
    logTarget_main: "主 Agent", logTarget_subagents: "默认子 Agent", logTarget_role: "命名角色",
    logError_configuration: "配置检查未通过", logError_file_access: "文件访问失败", logError_internal: "内部错误", logError_operation_failed: "操作未完成",
    logAction_open_switchboard: "打开面板", logAction_get_resolved_config: "读取配置", logAction_get_model_catalog: "读取模型目录",
    logAction_validate_config: "验证设置", logAction_diff_config: "预览更改", logAction_set_global_config: "写入全局设置",
    logAction_set_project_config: "写入项目设置", logAction_set_agent_role: "保存命名角色", logAction_delete_agent_role: "删除命名角色",
    logAction_reset_override: "清除此层覆盖",
  },
  en: {
    tokenRangeError: "Enter a whole number from {min} to {max} tokens.",
    subtitle: "Manage Codex models and agent settings", scopeTabs: "Configuration scope", project: "This project", global: "Global",
    scopeTitle: "Scope", globalDescription: "Saved in user config.toml", projectDescription: "Saved in project .codex/config.toml",
    agentType: "Agent type", mainAgent: "Main agent", defaultSubagents: "Default subagents",
    namedRole: "Named role", roleName: "Role name", rolePlaceholder: "For example, reviewer", roleHelp: "Start with a lowercase letter; use letters, numbers, hyphens, or underscores.",
    stepUpContext: "Increase context window", stepDownContext: "Decrease context window", stepUpCompact: "Increase auto-compaction threshold", stepDownCompact: "Decrease auto-compaction threshold",
    projectFolder: "Project folder", projectPlaceholder: "Enter the absolute project path",
    projectNeedPath: "Enter the absolute project path before reading or changing project settings.", globalScopeNote: "Global settings provide defaults across projects.",
    profileScopeNote: "Profile {profile} is active and may override some values in this file.",
    modelSection: "Model and reasoning", catalogNote: "From the local Codex model catalog", model: "Model", reasoning: "Reasoning effort", speed: "Speed",
    unchanged: "Leave this layer unchanged", currentModel: "Leave unchanged (current model: {value})", noModelChoice: "Choose a model", reasoningNoChangeCurrent: "Leave unchanged (effective: {value})", speedNoChange: "Leave this layer unchanged",
    speedStandard: "Standard", speedFast: "Fast",
    contextSection: "Context and auto-compaction", contextWindow: "Context window", compactLimit: "Auto-compaction threshold",
    inheritDefault: "Inherit Codex default",
    resultTitle: "Change preview", preparing: "Ready to apply", saved: "Settings saved",
    reset: "Clear this layer's overrides", refresh: "Refresh model list", preview: "Preview changes", apply: "Apply settings",
    footnote: "Settings are written directly to Codex's official TOML files; this plugin does not keep a separate settings store.",
    loadingSettings: "Reading settings…", loaded: "Codex model catalog and settings loaded.", loadingConfig: "Reading settings…", configReady: "Settings loaded; model catalog is still loading",
    projectLoaded: "Project settings loaded.", checking: "Checking settings…", validating: "Validating settings…", previewUpdated: "Preview updated.",
    catalogRefreshing: "Refreshing the model catalog…", catalogRefreshed: "Model catalog refreshed.", fallbackCatalog: "The local Codex catalog is unavailable; showing the conservative built-in model list.",
    commandCopied: "Launch command copied.", commandSelected: "Command selected; copy it from here.", commandGenerated: "Command generated; this conversation was not changed.",
    savedConfig: "Codex TOML settings updated.",
    overrideCleared: "Overrides cleared from this layer", layerCleared: "Overrides cleared from this layer.",
    reasoningUnknown: "This model is not in the selectable catalog, so its reasoning options are unknown.", reasoningNoLevels: "The catalog does not list reasoning options for this model.",
    reasoningUnsupported: "The current effort {value} is not supported by this model. Choose an available effort.", reasoningHelp: "Options follow the reasoning capabilities listed for this Codex model.",
    reasoningChanged: "This model does not support the current effort. Its default effort is selected; you can change it before applying.",
    reasoningAdjusted: "The current effort ({current}) is not supported. {selected} is selected for now; it is written only if you apply.",
    effort_none: "None", effort_low: "Low", effort_medium: "Medium", effort_high: "High", effort_xhigh: "Extra high", effort_max: "Max", effort_ultra: "Ultra",
    operationFailed: "Operation failed.",
    mainAgentPickerNote: "Choose the main agent's model, reasoning effort, and speed in the model picker at the lower right of the composer.",
    projectTrustWarning: "Codex loads project settings only for trusted projects. Confirm that this project is trusted before relying on these settings.",
    currentProjectLabel: "This project", globalLabel: "Global", roleTarget: "Named role: {name}",
    scopeMeta: "Configuration scope", agentMeta: "Agent type", fileMeta: "File to update",
    reviewApply: "Review and apply", reviewTitle: "Review configuration changes", reviewSubtitle: "Check the target and changed values. Nothing is written until you confirm.",
    reviewResetSubtitle: "This removes Agent Switchboard overrides from the selected layer.", resetReviewTitle: "Clear this layer's overrides?",
    reviewErrorTitle: "Could not prepare the preview", setting: "Setting", before: "Before", after: "After",
    backToEdit: "Back to editing", confirmApply: "Confirm and apply", confirmReset: "Clear this layer's overrides",
    close: "Close", noChanges: "There are no Agent Switchboard overrides to clear in this layer.", inheritValue: "Inherit from another layer or Codex default",
    reviewNoChanges: "These settings do not change any fields. Return to editing or close this window.",
    projectChanged: "Selected project settings loaded.", trustWarningTitle: "Project trust",
    setting_model: "Model", setting_reasoning: "Reasoning effort", setting_speed: "Speed",
    setting_context: "Context window", setting_compact: "Auto-compaction threshold",
    helpTitle: "Agent Switchboard guide",
    helpProject: "This project: settings are saved in the project's .codex/config.toml. Codex reads project settings only for trusted projects.",
    helpGlobal: "Global: settings are saved in the user config.toml as defaults. Project settings or command-line arguments can override them; clearing an override restores inheritance.",
    helpAgents: "Default subagents use the model and reasoning effort selected here. You can view, edit, and delete project and global named roles. Set the main agent's model, reasoning, and speed in the composer picker.",
    helpModel: "Models come from the local Codex catalog, and reasoning options depend on the selected model. Standard clears this layer's Fast setting; another layer may still enable Fast.",
    helpContext: "Blank fields inherit the current values shown in the boxes. Context ranges from 256,000 to the selected model's limit; steps are 10,000 tokens and align to the boundary near either limit. Values outside the range cannot be applied. Changing context updates the suggested compaction threshold, which you can edit.",
    helpTiming: "Model, reasoning, and speed settings apply to later requests. Context and compaction are read when a new agent starts. Context, compaction, and speed are shared layer settings and may affect other agents that inherit them.",
    helpReview: "Choose Review and apply to check the file, agent type, old and new values, and warnings. Settings are written only after confirmation. Expand an operation log to view written paths and values.",
    gotIt: "Got it", profileWarning: "The active profile {profile} has higher precedence and may override this setting.",
    sharedSettingWarning: "Context, auto-compaction, and speed are shared layer settings and may affect the main agent or other agents inheriting this layer.",
    clearFastWarning: "Removing this layer's Fast override may leave a lower-precedence Fast setting active.",
    manageRoles: "View existing roles", rolesTitle: "Existing roles", projectRoles: "Project roles", globalRoles: "Global roles",
    rolesLoading: "Loading roles…", rolesEmpty: "No named roles yet", rolesNeedProject: "Enter a project folder to view project roles",
    editRole: "Edit", deleteRole: "Delete", deleteRoleTitle: "Delete named role", cancel: "Cancel",
    deleteRolePrompt: "Delete the {scope} configuration for “{name}”?",
    deleteRoleWarning: "This removes the role declaration from this scope. Its default role config file is also deleted; custom or shared files are kept.",
    deleteRoleFiles: "Files involved",
    roleDeleted: "Deleted role “{name}”", roleReloadFailed: "The role was deleted, but the list could not be refreshed.", roleNoSettings: "No role-specific settings; inherited values apply",
    roleDeleteCustomKept: "Role deleted. Its custom config file was kept.", roleDeleteSharedKept: "Role deleted. Its shared config file was kept.",
    roleDeleteFileFailed: "Role deleted, but its default config file could not be deleted.",
    openLogs: "Operation log", logsTitle: "Operation log",
    refreshLogs: "Refresh log", logsLoading: "Loading log…", logsEmpty: "No operations recorded", logsFailed: "Could not read the plugin log.",
    logResult_success: "Succeeded", logResult_error: "Failed", logDuration: "{value} ms", logDetails: "View details",
    logRoleName: "Role", logFilesWritten: "Files written", logFilesDeleted: "Files deleted", logPreservedFile: "Preserved file",
    logOrphanedFile: "Orphaned role file", logSettingsWritten: "Settings written", logSettingsBefore: "Previous settings", logSettingsRemoved: "Settings removed", logChangedSettings: "Changed fields",
    logScope_project: "Project", logScope_global: "Global",
    logTarget_main: "Main agent", logTarget_subagents: "Default subagents", logTarget_role: "Named role",
    logError_configuration: "Configuration check failed", logError_file_access: "File access failed", logError_internal: "Internal error", logError_operation_failed: "Operation did not complete",
    logAction_open_switchboard: "Opened panel", logAction_get_resolved_config: "Read configuration", logAction_get_model_catalog: "Read model catalog",
    logAction_validate_config: "Validated settings", logAction_diff_config: "Previewed changes", logAction_set_global_config: "Saved global settings",
    logAction_set_project_config: "Saved project settings", logAction_set_agent_role: "Saved named role", logAction_delete_agent_role: "Deleted named role",
    logAction_reset_override: "Cleared layer overrides",
  },
};

const byId = (id) => document.getElementById(id);
const statusEl = byId("status");
const reviewDialog = byId("review-dialog");
const helpDialog = byId("help-dialog");
const rolesDialog = byId("roles-dialog");
const roleDeleteDialog = byId("role-delete-dialog");
const logsDialog = byId("logs-dialog");
const customSelects = new Map();

function t(key, values = {}) {
  let message = COPY[state.language]?.[key] ?? COPY.en[key] ?? key;
  for (const [name, value] of Object.entries(values)) message = message.replaceAll(`{${name}}`, String(value));
  return message;
}

function trimMainEnding(text) {
  return String(text).replace(/[。.]+\s*$/u, "").trimEnd();
}

function applyLocale(locale) {
  const preferred = (locale || navigator.language || document.documentElement.lang || "zh-CN").toLowerCase();
  state.language = preferred.startsWith("zh") ? "zh" : "en";
  document.documentElement.lang = state.language === "zh" ? "zh-CN" : "en";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const message = t(node.dataset.i18n);
    node.textContent = node.closest(".shell") && !node.closest("dialog") ? trimMainEnding(message) : message;
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => { node.placeholder = t(node.dataset.i18nPlaceholder); });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((node) => { node.setAttribute("aria-label", t(node.dataset.i18nAriaLabel)); });
  if (state.statusKey) setLocalizedStatus(state.statusKey, state.statusKind, state.statusValues);
}

function updateStatus(message, kind = "") {
  statusEl.textContent = trimMainEnding(message);
  statusEl.style.color = kind === "error" ? "var(--bad)" : kind === "good" ? "var(--good)" : kind === "warn" ? "var(--warn)" : "";
}

function setStatus(message, kind = "") {
  state.statusKey = null;
  updateStatus(message, kind);
}

function setLocalizedStatus(key, kind = "", values = {}) {
  state.statusKey = key;
  state.statusValues = values;
  state.statusKind = kind;
  updateStatus(t(key, values), kind);
}

function setTheme(theme) {
  if (theme === "dark" || theme === "light") {
    document.documentElement.dataset.theme = theme;
  } else {
    delete document.documentElement.dataset.theme;
  }
}

function applyHostContext(context = {}) {
  setTheme(context.theme);
  if (context.theme === "dark" || context.theme === "light") applyDocumentTheme(context.theme);
  if (context.styles?.variables) applyHostStyleVariables(context.styles.variables);
  if (context.styles?.css?.fonts) applyHostFonts(context.styles.css.fonts);
  applyLocale(context.locale);
  renderScopeCopy();
  renderModelOptions();
  renderContextBounds();
  syncAllCustomSelects();
}

function parseToolResult(result) {
  if (result?.structuredContent && typeof result.structuredContent === "object") {
    return result.structuredContent;
  }
  const textBlock = result?.content?.find((item) => item.type === "text")?.text;
  if (typeof textBlock === "string") {
    try {
      return JSON.parse(textBlock);
    } catch {
      return { ok: !result?.isError, message: textBlock };
    }
  }
  return { ok: !result?.isError };
}

async function callTool(name, args = {}) {
  const raw = await app.callServerTool({ name, arguments: args });
  const parsed = parseToolResult(raw);
  if (raw?.isError || parsed?.ok === false) {
    throw new Error(parsed.error || parsed.errors?.join("; ") || t("operationFailed"));
  }
  return parsed;
}

function addOption(select, value, label, disabled = false) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  option.disabled = disabled;
  select.append(option);
}

function selectedLayer() {
  if (state.scope === "project" && state.projectRoot) return state.config?.layers?.project;
  return state.config?.layers?.global;
}

function activeSettings() {
  if (state.target === "role") {
    const roleName = byId("role-name").value.trim();
    const roleScope = state.scope === "project" ? "project" : "global";
    return state.config?.roleLayers?.[roleScope]?.[roleName]?.settings || {};
  }
  const layer = selectedLayer();
  return layer?.[state.target] || {};
}

function effectiveSettings() {
  if (!state.config) return {};
  if (state.target === "role") {
    const roleName = byId("role-name").value.trim();
    const inherited = state.config.effective?.subagents || {};
    const role = state.config.effective?.roles?.[roleName]?.settings || {};
    return { ...inherited, ...role };
  }
  return state.config.effective?.[state.target] || {};
}

function currentField(source, field) {
  if (field === "model" && state.target === "subagents") return source["agents.default_subagent_model"];
  if (field === "model" && state.target === "role") {
    return source.model ?? source["agents.default_subagent_model"];
  }
  if (field === "reasoning_effort" && state.target === "subagents") {
    return source["agents.default_subagent_reasoning_effort"];
  }
  if (field === "reasoning_effort" && state.target === "role") {
    return source.model_reasoning_effort ?? source["agents.default_subagent_reasoning_effort"];
  }
  if (field === "reasoning_effort") return source.model_reasoning_effort;
  return source[field];
}

function showInheritedHint(id, value) {
  const node = byId(id);
  const numeric = typeof value === "number" ? value
    : typeof value === "string" && /^\d+$/.test(value) ? Number(value) : null;
  const formatted = numeric === null
    ? value
    : numeric.toLocaleString(state.language === "zh" ? "zh-CN" : "en-US");
  node.textContent = value ? t("effectiveValue", { value: formatted }) : "";
}

function modelById(id) {
  return state.catalog.find((model) => model.id === id);
}

function modelLabel(id) {
  if (!id) return "";
  const label = modelById(id)?.label || id;
  return label.replace(/^(GPT-\d+(?:\.\d+)?)-([A-Z])/, "$1 $2");
}

function reasoningLabel(level) {
  return COPY[state.language]?.[`effort_${level}`] || level;
}

function formatTokenCount(value) {
  return Number(value).toLocaleString(state.language === "zh" ? "zh-CN" : "en-US");
}

function renderReasoningOptions(model, activeEffort, effectiveEffort) {
  const reasoning = byId("reasoning");
  const levels = Array.isArray(model?.reasoningEfforts) ? model.reasoningEfforts : [];
  const previous = state.pendingReasoning !== undefined ? state.pendingReasoning : activeEffort;
  const current = activeEffort || effectiveEffort;
  const noChangeDisabled = Boolean(model && current && !levels.includes(current));
  reasoning.replaceChildren();
  addOption(
    reasoning,
    "",
    current ? t("reasoningNoChangeCurrent", { value: reasoningLabel(current) }) : t("unchanged"),
    noChangeDisabled,
  );
  for (const level of levels) addOption(reasoning, level, reasoningLabel(level));
  reasoning.value = levels.includes(previous) ? previous : "";
  reasoning.disabled = !model || levels.length === 0;

  const help = byId("reasoning-help");
  if (!model) help.textContent = t("reasoningUnknown");
  else if (!levels.length) help.textContent = t("reasoningNoLevels");
  else if (noChangeDisabled && levels.includes(reasoning.value)) {
    help.textContent = t("reasoningAdjusted", { current: reasoningLabel(current), selected: reasoningLabel(reasoning.value) });
  } else if (noChangeDisabled) help.textContent = t("reasoningUnsupported", { value: reasoningLabel(current) });
  else help.textContent = "";
  help.textContent = trimMainEnding(help.textContent);
}

function renderModelOptions() {
  const select = byId("model");
  const previous = state.pendingModel !== undefined ? state.pendingModel : select.value;
  const activeModel = currentField(activeSettings(), "model");
  const effectiveModel = currentField(effectiveSettings(), "model") || activeModel;
  select.replaceChildren();
  addOption(select, "", effectiveModel ? t("currentModel", { value: modelLabel(effectiveModel) }) : t("unchanged"));
  for (const model of state.catalog) addOption(select, model.id, modelLabel(model.id));
  const desired = state.pendingModel !== undefined
    ? state.pendingModel
    : (state.catalog.some((model) => model.id === activeModel) ? activeModel : "");
  select.value = state.catalog.some((model) => model.id === desired) ? desired : "";

  const selectedId = select.value || activeModel || effectiveModel;
  const selected = modelById(selectedId);
  const activeEffort = currentField(activeSettings(), "reasoning_effort");
  const effectiveEffort = currentField(effectiveSettings(), "reasoning_effort") || activeEffort;
  renderReasoningOptions(selected, activeEffort, effectiveEffort);
  syncCustomSelect("model");
  syncCustomSelect("reasoning");
}

function selectedModel() {
  const activeModel = currentField(activeSettings(), "model");
  const effectiveModel = currentField(effectiveSettings(), "model") || activeModel;
  const selectedId = byId("model").value || effectiveModel;
  return modelById(selectedId);
}

function renderContextBounds() {
  const model = selectedModel();
  const contextInput = byId("context-window");
  const compactInput = byId("compact-limit");
  const effective = effectiveSettings();
  const maximum = Number.isInteger(model?.maxContextWindow)
    ? model.maxContextWindow
    : Number.isInteger(model?.contextWindow) ? model.contextWindow : 872000;
  const minimum = Math.min(256000, maximum);
  contextInput.min = String(minimum);
  contextInput.max = String(maximum);
  contextInput.step = "1";

  const configuredContext = Number(contextInput.value);
  const modelDefault = Number.isInteger(model?.contextWindow)
    && model.contextWindow >= minimum && model.contextWindow <= maximum
    ? model.contextWindow
    : null;
  const inheritedContext = Number(effective.model_context_window);
  const contextPlaceholderValue = Number.isInteger(inheritedContext)
    && inheritedContext >= minimum && inheritedContext <= maximum
    ? inheritedContext
    : modelDefault;
  const baseContext = Number.isInteger(configuredContext) && configuredContext > 0
    ? Math.min(maximum, Math.max(minimum, configuredContext))
    : contextPlaceholderValue || maximum;
  const compactMaximum = Math.max(10000, Math.floor(baseContext * (model?.autoCompactPercent || 90) / 100));
  compactInput.min = "10000";
  compactInput.max = String(compactMaximum);
  compactInput.step = "1";
  const effectiveCompact = Number(effective.model_auto_compact_token_limit);
  const compactPlaceholderValue = Number.isInteger(effectiveCompact)
    && effectiveCompact >= 10000 && effectiveCompact <= compactMaximum
    ? effectiveCompact
    : contextPlaceholderValue
      ? compactMaximum
      : null;
  const contextUsesPlaceholder = !contextInput.value;
  const compactUsesPlaceholder = !compactInput.value;
  contextInput.placeholder = contextUsesPlaceholder && contextPlaceholderValue
    ? formatTokenCount(contextPlaceholderValue)
    : t("inheritDefault");
  compactInput.placeholder = compactUsesPlaceholder && compactPlaceholderValue
    ? formatTokenCount(compactPlaceholderValue)
    : t("inheritDefault");
  contextInput.classList.toggle("has-effective-placeholder", contextUsesPlaceholder && Boolean(contextPlaceholderValue));
  compactInput.classList.toggle("has-effective-placeholder", compactUsesPlaceholder && Boolean(compactPlaceholderValue));
  updateTokenInputValidity(contextInput);
  updateTokenInputValidity(compactInput);
  return { model, baseContext, compactMaximum };
}

function suggestCompactLimit() {
  const context = byId("context-window").value.trim();
  const compact = byId("compact-limit");
  if (!context) {
    if (!state.compactManuallyEdited) compact.value = "";
    renderContextBounds();
    return;
  }
  if (!updateTokenInputValidity(byId("context-window"))) {
    renderContextBounds();
    return;
  }
  const numeric = Number(context);
  if (!Number.isInteger(numeric) || numeric <= 0) return;
  const percent = selectedModel()?.autoCompactPercent || 90;
  const recommended = Math.floor(numeric * percent / 100);
  if (!state.compactManuallyEdited) {
    compact.value = String(recommended);
  }
  renderContextBounds();
}

function updateTokenInputValidity(input) {
  const valueText = input.value.trim();
  let message = "";
  if (valueText) {
    const value = Number(valueText);
    const minimum = Number(input.min);
    const maximum = Number(input.max);
    if (!Number.isInteger(value) || value < minimum || value > maximum) {
      const locale = state.language === "zh" ? "zh-CN" : "en-US";
      message = t("tokenRangeError", {
        min: Number.isFinite(minimum) ? minimum.toLocaleString(locale) : input.min,
        max: Number.isFinite(maximum) ? maximum.toLocaleString(locale) : input.max,
      });
    }
  }
  input.setCustomValidity(message);
  input.setAttribute("aria-invalid", String(Boolean(message)));
  return !message;
}

function validateTokenInputs() {
  for (const input of [byId("context-window"), byId("compact-limit")]) {
    if (updateTokenInputValidity(input)) continue;
    input.focus();
    input.reportValidity();
    return false;
  }
  return true;
}

function stepTokenInput(input, direction) {
  if (!input) return;
  const minimum = Number(input.min);
  const maximum = Number(input.max);
  const step = Number(input.dataset.tokenStep) || 10000;
  const currentText = input.value.trim();
  const inheritedText = input.placeholder.replaceAll(",", "").match(/^\s*\d+\s*$/);
  const current = currentText
    ? Number(currentText)
    : inheritedText ? Number(inheritedText[0]) : direction > 0 ? minimum : maximum;
  const next = current < minimum
    ? minimum
    : current > maximum
      ? maximum
      : direction > 0
        ? Math.min(maximum, current + step)
        : Math.max(minimum, current - step);
  if (next === current) return;
  input.value = String(next);
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
}

function renderScopeCopy() {
  const notice = byId("scope-notice");
  if (state.scope === "global") {
    byId("scope-description").textContent = t("globalDescription");
    let message = t("globalScopeNote");
    if (state.config?.selectedProfile) message += ` ${t("profileScopeNote", { profile: state.config.selectedProfile })}`;
    notice.textContent = trimMainEnding(message);
    notice.className = "help scope-help";
    notice.hidden = false;
  } else if (state.scope === "project") {
    byId("scope-description").textContent = t("projectDescription");
    notice.textContent = state.projectRoot ? "" : trimMainEnding(t("projectNeedPath"));
    notice.className = state.projectRoot ? "help scope-help" : "help scope-help scope-error";
    notice.hidden = Boolean(state.projectRoot);
  }
}

function renderForm() {
  byId("role-field").hidden = state.target !== "role";
  byId("project-field").hidden = state.scope !== "project";
  byId("model-section").hidden = state.target === "main";
  byId("main-agent-note").hidden = state.target !== "main";
  renderScopeCopy();

  const layer = activeSettings();
  const effective = effectiveSettings();
  renderModelOptions();
  byId("speed").value = "";
  if (layer.service_tier === "fast") byId("speed").value = "fast";
  else if (Object.prototype.hasOwnProperty.call(layer, "service_tier")) byId("speed").value = "standard";
  byId("context-window").value = layer.model_context_window ?? "";
  byId("compact-limit").value = layer.model_auto_compact_token_limit ?? "";
  state.compactManuallyEdited = false;
  showInheritedHint("model-inherited", "");
  showInheritedHint("reasoning-inherited", "");
  renderContextBounds();
  syncCustomSelect("target");
  syncCustomSelect("speed");
}

async function loadConfig({ includeRoles = state.target === "role" } = {}) {
  const root = state.projectRoot;
  const sequence = ++state.configLoadSequence;
  const args = {};
  if (root) args.project_root = root;
  args.include_roles = includeRoles;
  const config = await callTool("get_resolved_config", args);
  if (sequence !== state.configLoadSequence || root !== state.projectRoot) return config;
  state.config = config;
  renderForm();
  return config;
}

function roleSummary(settings = {}) {
  const values = [];
  if (settings.model) values.push(`${t("setting_model")}: ${modelLabel(settings.model)}`);
  if (settings.model_reasoning_effort) values.push(`${t("setting_reasoning")}: ${reasoningLabel(settings.model_reasoning_effort)}`);
  if (settings.service_tier) values.push(`${t("setting_speed")}: ${settings.service_tier === "fast" ? t("speedFast") : settings.service_tier}`);
  if (Number.isInteger(settings.model_context_window)) values.push(`${t("setting_context")}: ${formatTokenCount(settings.model_context_window)}`);
  if (Number.isInteger(settings.model_auto_compact_token_limit)) values.push(`${t("setting_compact")}: ${formatTokenCount(settings.model_auto_compact_token_limit)}`);
  return values.length ? values.join(" · ") : t("roleNoSettings");
}

function renderRoleGroup(scope, listId) {
  const container = byId(listId);
  container.replaceChildren();
  if (scope === "project" && !state.projectRoot) {
    const empty = document.createElement("p");
    empty.className = "role-empty";
    empty.textContent = t("rolesNeedProject");
    container.append(empty);
    return;
  }

  const roles = state.config?.roleLayers?.[scope] || {};
  const entries = Object.entries(roles).sort(([left], [right]) => left.localeCompare(right));
  if (!entries.length) {
    const empty = document.createElement("p");
    empty.className = "role-empty";
    empty.textContent = t("rolesEmpty");
    container.append(empty);
    return;
  }

  for (const [name, role] of entries) {
    const item = document.createElement("article");
    item.className = "role-item";
    const main = document.createElement("div");
    main.className = "role-main";
    const title = document.createElement("strong");
    title.textContent = name;
    const summary = document.createElement("div");
    summary.className = "role-summary";
    summary.textContent = roleSummary(role?.settings);
    main.append(title, summary);

    const actions = document.createElement("div");
    actions.className = "role-actions";
    for (const [action, label, className] of [
      ["edit", t("editRole"), "btn"],
      ["delete", t("deleteRole"), "btn danger"],
    ]) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = className;
      button.dataset.roleAction = action;
      button.dataset.roleName = name;
      button.dataset.roleScope = scope;
      button.textContent = label;
      button.setAttribute("aria-label", `${label}: ${name}`);
      actions.append(button);
    }
    item.append(main, actions);
    container.append(item);
  }
}

function renderRoleManager() {
  renderRoleGroup("project", "project-role-list");
  renderRoleGroup("global", "global-role-list");
}

function setRoleManagerStatus(message, kind = "good") {
  const status = byId("roles-status");
  status.className = `notice role-status ${kind}`;
  status.textContent = message;
  status.hidden = !message;
}

async function openRoleManager() {
  setRoleManagerStatus(t("rolesLoading"), "");
  renderRoleManager();
  rolesDialog.showModal();
  try {
    await loadConfig({ includeRoles: true });
    renderRoleManager();
    setRoleManagerStatus("");
  } catch (error) {
    setRoleManagerStatus(error.message || t("operationFailed"), "error");
  }
}

async function editManagedRole(scope, name) {
  clearPendingChoices();
  state.scope = scope;
  state.target = "role";
  document.querySelectorAll(".scope-tab").forEach((button) => {
    button.setAttribute("aria-selected", String(button.dataset.scope === scope));
  });
  byId("target").value = "role";
  byId("role-name").value = name;
  rolesDialog.close();
  renderForm();
  try {
    await loadConfig();
  } catch (error) {
    setStatus(error.message || t("operationFailed"), "error");
  }
}

function confirmRoleDelete(scope, name) {
  state.pendingRoleDelete = { scope, name };
  byId("role-delete-copy").textContent = t("deleteRolePrompt", {
    name,
    scope: t(scope === "project" ? "currentProjectLabel" : "globalLabel"),
  });
  const warning = byId("role-delete-warning");
  warning.className = "notice warn";
  warning.textContent = t("deleteRoleWarning");
  const fileList = byId("role-delete-files");
  fileList.replaceChildren();
  const roleData = state.config?.roleLayers?.[scope]?.[name];
  const files = [state.config?.configFiles?.[scope], ...(roleData?.configFiles || [])].filter(Boolean);
  if (files.length) {
    const label = document.createElement("span");
    label.className = "file-label";
    label.textContent = t("deleteRoleFiles");
    fileList.append(label);
    for (const file of files) {
      const line = document.createElement("span");
      line.textContent = file;
      fileList.append(line);
    }
  }
  roleDeleteDialog.showModal();
}

async function deleteSelectedRole() {
  const pending = state.pendingRoleDelete;
  if (!pending) return;
  const confirm = byId("role-delete-confirm");
  confirm.disabled = true;
  try {
    const result = await callTool("delete_agent_role", {
      scope: pending.scope,
      role_name: pending.name,
      ...(state.projectRoot ? { project_root: state.projectRoot } : {}),
    });
    roleDeleteDialog.close();
    state.pendingRoleDelete = null;
    try {
      await loadConfig();
    } catch {
      setRoleManagerStatus(`${t("roleDeleted", { name: pending.name })} ${t("roleReloadFailed")}`, "warn");
      setLocalizedStatus("roleDeleted", "good", { name: pending.name });
      return;
    }
    renderRoleManager();
    const messages = (result.warnings || []).map((warning) => {
      if (warning.startsWith("The role config file is shared")) return t("roleDeleteSharedKept");
      if (warning.startsWith("The role uses a custom config_file")) return t("roleDeleteCustomKept");
      if (warning.startsWith("The role was removed, but its default config file")) return t("roleDeleteFileFailed");
      return warning;
    });
    setRoleManagerStatus([t("roleDeleted", { name: pending.name }), ...messages].join(" "), messages.length ? "warn" : "good");
    setLocalizedStatus("roleDeleted", "good", { name: pending.name });
  } catch (error) {
    const warning = byId("role-delete-warning");
    warning.className = "notice error";
    warning.textContent = error.message || t("operationFailed");
  } finally {
    confirm.disabled = false;
  }
}

function renderLogs(entries) {
  const list = byId("logs-list");
  list.replaceChildren();
  if (!entries.length) {
    const empty = document.createElement("p");
    empty.className = "role-empty";
    empty.textContent = t("logsEmpty");
    list.append(empty);
    return;
  }
  for (const [index, entry] of entries.entries()) {
    const item = document.createElement("article");
    item.className = "log-item";
    const resultClass = entry.result === "success" ? "success" : "error";
    item.dataset.result = resultClass;
    const head = document.createElement("div");
    head.className = "log-item-head";
    const event = document.createElement("span");
    event.className = `log-event ${resultClass}`;
    event.textContent = t(`logAction_${entry.event}`) === `logAction_${entry.event}`
      ? String(entry.event || "")
      : t(`logAction_${entry.event}`);
    const time = document.createElement("time");
    time.className = "log-time";
    time.dateTime = entry.timestamp;
    const date = new Date(entry.timestamp);
    time.textContent = Number.isNaN(date.getTime())
      ? String(entry.timestamp)
      : date.toLocaleString(state.language === "zh" ? "zh-CN" : "en-US");
    head.append(event, time);

    const meta = document.createElement("div");
    meta.className = "log-meta";
    const result = document.createElement("span");
    result.className = `log-result ${resultClass}`;
    result.textContent = t(`logResult_${entry.result}`);
    meta.append(result);
    for (const key of ["scope", "target", "errorCode"]) {
      if (!entry[key]) continue;
      const label = document.createElement("span");
      label.textContent = t(`${key === "errorCode" ? "logError" : `log${key[0].toUpperCase()}${key.slice(1)}`}_${entry[key]}`);
      meta.append(label);
    }
    if (Number.isFinite(entry.durationMs)) {
      const duration = document.createElement("span");
      duration.textContent = t("logDuration", { value: Math.max(0, Math.round(entry.durationMs)) });
      meta.append(duration);
    }
    const changeDetails = entry.details && typeof entry.details === "object" ? entry.details : null;
    let hasDetails = false;
    if (changeDetails) {
      const rows = [];
      const addRow = (labelKey, value) => {
        if (value === undefined || value === null || value === "") return;
        const rendered = Array.isArray(value)
          ? value.map((part) => typeof part === "string" ? part : JSON.stringify(part)).join("\n")
          : typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);
        if (rendered) rows.push([t(labelKey), rendered]);
      };
      addRow("logRoleName", changeDetails.roleName);
      addRow("logFilesWritten", changeDetails.filesWritten);
      addRow("logFilesDeleted", changeDetails.filesDeleted);
      addRow("logPreservedFile", changeDetails.preservedConfigFile);
      addRow("logOrphanedFile", changeDetails.orphanedRoleConfig);
      addRow("logSettingsWritten", changeDetails.settingsWritten);
      addRow("logSettingsBefore", changeDetails.settingsBeforeRemoval);
      addRow("logSettingsRemoved", changeDetails.settingsRemoved || changeDetails.removedSettings);
      addRow("logChangedSettings", changeDetails.changedSettings);
      if (rows.length) {
        hasDetails = true;
        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "log-item-toggle";
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-controls", `log-detail-${index}`);
        toggle.append(head, meta);

        const panel = document.createElement("div");
        panel.className = "log-detail-panel";
        panel.id = `log-detail-${index}`;
        panel.setAttribute("aria-hidden", "true");
        panel.inert = true;
        const inner = document.createElement("div");
        inner.className = "log-detail-inner";
        const body = document.createElement("div");
        body.className = "log-details-body";
        for (const [labelText, valueText] of rows) {
          const row = document.createElement("div");
          row.className = "log-detail-row";
          const label = document.createElement("span");
          label.className = "log-detail-label";
          label.textContent = labelText;
          const value = document.createElement("span");
          value.className = "log-detail-value";
          value.textContent = valueText;
          row.append(label, value);
          body.append(row);
        }
        inner.append(body);
        panel.append(inner);
        toggle.addEventListener("click", () => {
          const expanded = toggle.getAttribute("aria-expanded") !== "true";
          toggle.setAttribute("aria-expanded", String(expanded));
          item.dataset.expanded = String(expanded);
          panel.setAttribute("aria-hidden", String(!expanded));
          panel.inert = !expanded;
        });
        item.append(toggle, panel);
      }
    }
    if (!hasDetails) {
      const summary = document.createElement("div");
      summary.className = "log-item-summary";
      summary.append(head, meta);
      item.append(summary);
    }
    list.append(item);
  }
}

async function loadPluginLogs() {
  const list = byId("logs-list");
  const error = byId("logs-error");
  error.hidden = true;
  list.replaceChildren();
  const loading = document.createElement("p");
  loading.className = "role-empty";
  loading.textContent = t("logsLoading");
  list.append(loading);
  try {
    const result = await callTool("get_plugin_logs", { limit: 100 });
    renderLogs(Array.isArray(result.entries) ? result.entries : []);
  } catch (cause) {
    list.replaceChildren();
    error.textContent = cause.message || t("logsFailed");
    error.hidden = false;
  }
}

async function loadCatalog(refresh = false) {
  const catalog = await callTool("get_model_catalog", { refresh });
  state.catalog = Array.isArray(catalog.models) ? catalog.models : [];
  renderModelOptions();
  renderContextBounds();
  return catalog;
}

function collectSettings() {
  const settings = {};
  if (state.target !== "main") {
    if (byId("model").value) settings.model = byId("model").value;
    if (byId("reasoning").value) settings.reasoning_effort = byId("reasoning").value;
    if (byId("speed").value) settings.speed = byId("speed").value;
  }
  if (byId("context-window").value) settings.model_context_window = Number(byId("context-window").value);
  if (byId("compact-limit").value) settings.model_auto_compact_token_limit = Number(byId("compact-limit").value);
  return settings;
}

function normalizeProjectRoot(value) {
  let root = String(value ?? "").trim();
  if (root.length >= 2 && ((root.startsWith('"') && root.endsWith('"')) || (root.startsWith("'") && root.endsWith("'")))) {
    root = root.slice(1, -1).trim();
  }
  return root;
}

function requestArgs(settings = collectSettings()) {
  const args = {
    scope: state.scope,
    target: state.target,
    settings,
  };
  if (state.projectRoot) args.project_root = state.projectRoot;
  if (state.target === "role" && byId("role-name").value.trim()) {
    args.role_name = byId("role-name").value.trim();
  }
  return args;
}

function settingLabel(setting) {
  const key = setting === "agents.default_subagent_model" ? "setting_model"
    : setting === "agents.default_subagent_reasoning_effort" ? "setting_reasoning"
      : setting === "model" ? "setting_model"
        : setting === "model_reasoning_effort" ? "setting_reasoning"
          : setting === "service_tier" ? "setting_speed"
            : setting === "model_context_window" ? "setting_context"
              : setting === "model_auto_compact_token_limit" ? "setting_compact" : "";
  return key ? t(key) : setting;
}

function formatChangeValue(setting, value) {
  const text = String(value);
  if (text === "(unset)" || text === "null" || text === "undefined") return t("inheritValue");
  if (setting.includes("context_window") || setting.includes("compact_token_limit")) {
    const numeric = Number(text);
    if (Number.isFinite(numeric)) return `${numeric.toLocaleString(state.language === "zh" ? "zh-CN" : "en-US")} tokens`;
  }
  if (setting.includes("model") && !setting.includes("reasoning")) return modelLabel(text);
  if (setting.includes("reasoning")) return reasoningLabel(text);
  if (setting === "service_tier") return text === "fast" ? t("speedFast") : text;
  return text;
}

function localizedWarning(message) {
  if (/project.{0,80}trusted|trusted.{0,80}project/i.test(message)) return t("projectTrustWarning");
  if (message.startsWith("Context, compaction, and service tier are standard config fields")) return t("sharedSettingWarning");
  if (message.startsWith("Standard removes this layer's Fast override")) return t("clearFastWarning");
  const profileMatch = message.match(/^The selected profile ['"]?(.+?)['"]? has higher precedence/);
  if (profileMatch) return t("profileWarning", { profile: profileMatch[1] });
  return message;
}

function targetLabel(target = state.target, roleName = byId("role-name").value.trim()) {
  if (target === "main") return t("mainAgent");
  if (target === "subagents") return t("defaultSubagents");
  return t("roleTarget", { name: roleName || t("namedRole") });
}

function appendReviewMeta(label, value, className = "") {
  const item = document.createElement("div");
  if (className) item.className = className;
  const caption = document.createElement("span");
  const content = document.createElement("strong");
  caption.textContent = label;
  if (Array.isArray(value)) {
    for (const line of value) {
      const item = document.createElement("span");
      item.className = "meta-file-line";
      item.textContent = line;
      content.append(item);
    }
  } else {
    content.textContent = value;
  }
  item.append(caption, content);
  byId("review-meta").append(item);
}

function openReview(result, action, request = requestArgs(), resetKeys = []) {
  state.pendingReview = { result, action, request, resetKeys };
  byId("review-title").textContent = action === "error" ? t("reviewErrorTitle")
    : action === "reset" ? t("resetReviewTitle") : t("reviewTitle");
  byId("review-subtitle").textContent = action === "reset" ? t("reviewResetSubtitle") : t("reviewSubtitle");
  const meta = byId("review-meta");
  meta.replaceChildren();
  appendReviewMeta(t("scopeMeta"), state.scope === "project" ? t("currentProjectLabel") : t("globalLabel"));
  appendReviewMeta(t("agentMeta"), targetLabel(request.target, request.role_name));
  const files = result.filesAffected || [];
  appendReviewMeta(t("fileMeta"), files.length ? files : t(state.scope === "project" ? "projectDescription" : "globalDescription"), "meta-file");

  const rows = byId("review-rows");
  rows.replaceChildren();
  for (const change of result.changes || []) {
    const row = document.createElement("tr");
    const name = document.createElement("td");
    const before = document.createElement("td");
    const after = document.createElement("td");
    name.textContent = settingLabel(change.setting);
    before.textContent = formatChangeValue(change.setting, change.before);
    after.textContent = formatChangeValue(change.setting, change.after);
    row.append(name, before, after);
    rows.append(row);
  }
  const hasChanges = Boolean((result.changes || []).length);
  byId("review-table-wrap").hidden = !hasChanges;
  const emptyMessage = byId("review-empty");
  emptyMessage.hidden = hasChanges || action === "error";
  if (!hasChanges && action !== "error") {
    emptyMessage.textContent = t(action === "reset" ? "noChanges" : "reviewNoChanges");
  }

  const warningContainer = byId("review-warnings");
  warningContainer.replaceChildren();
  const warnings = [...(result.warnings || [])];
  if (state.scope === "project") warnings.unshift("Codex loads project config only when the project is trusted.");
  const uniqueWarnings = [...new Set(warnings.map(localizedWarning))];
  for (const warning of uniqueWarnings) {
    const item = document.createElement("div");
    item.className = `notice ${action === "error" ? "error" : "warn"}`;
    item.textContent = warning;
    warningContainer.append(item);
  }
  const confirm = byId("review-confirm");
  confirm.textContent = t(action === "reset" ? "confirmReset" : "confirmApply");
  confirm.hidden = action === "error";
  confirm.disabled = action !== "error" && !(result.changes || []).length;
  if (!reviewDialog.open) reviewDialog.showModal();
}

async function preview() {
  if (!validateTokenInputs()) return;
  setLocalizedStatus("checking");
  const request = requestArgs();
  try {
    await callTool("validate_config", request);
    const result = await callTool("diff_config", request);
    openReview(result, "apply", request);
    setLocalizedStatus("previewUpdated", "good");
  } catch (error) {
    openReview({ changes: [], warnings: [error.message], filesAffected: [] }, "error", request);
    setStatus(error.message, "error");
  }
}

function clearPendingChoices() {
  state.pendingModel = undefined;
  state.pendingReasoning = undefined;
}

async function applyReviewed() {
  const pending = state.pendingReview;
  if (!pending || pending.action === "error") return;
  const confirm = byId("review-confirm");
  confirm.disabled = true;
  setLocalizedStatus("validating");
  try {
    const request = pending.request;
    if (pending.action === "reset") {
      await callTool("reset_override", {
        scope: request.scope,
        target: request.target,
        keys: pending.resetKeys,
        ...(request.project_root ? { project_root: request.project_root } : {}),
        ...(request.role_name ? { role_name: request.role_name } : {}),
      });
      reviewDialog.close();
      clearPendingChoices();
      await loadConfig();
      setLocalizedStatus("layerCleared", "good");
      return;
    }

    if (request.target === "role") {
      await callTool("set_agent_role", {
        scope: request.scope,
        role_name: request.role_name,
        settings: request.settings,
        ...(request.project_root ? { project_root: request.project_root } : {}),
      });
    } else if (request.scope === "global") {
      await callTool("set_global_config", { target: request.target, settings: request.settings });
    } else {
      await callTool("set_project_config", {
        project_root: request.project_root,
        target: request.target,
        settings: request.settings,
      });
    }
    reviewDialog.close();
    clearPendingChoices();
    await loadConfig();
    setLocalizedStatus("savedConfig", "good");
  } catch (error) {
    openReview({ changes: [], warnings: [error.message], filesAffected: [] }, "error", pending.request);
    setStatus(error.message, "error");
  } finally {
    confirm.disabled = false;
  }
}

async function resetLayer() {
  const resetKeys = state.target === "main"
    ? ["model_context_window", "model_auto_compact_token_limit"]
    : ["model", "reasoning_effort", "speed", "model_context_window", "model_auto_compact_token_limit"];
  const resetSettings = {};
  if (resetKeys.includes("model")) resetSettings.model = null;
  if (resetKeys.includes("reasoning_effort")) resetSettings.reasoning_effort = null;
  if (resetKeys.includes("speed")) resetSettings.speed = "standard";
  if (resetKeys.includes("model_context_window")) resetSettings.model_context_window = null;
  if (resetKeys.includes("model_auto_compact_token_limit")) resetSettings.model_auto_compact_token_limit = null;
  const request = requestArgs(resetSettings);
  try {
    const result = await callTool("diff_config", request);
    const source = activeSettings();
    const fieldByKey = {
      model: state.target === "subagents" ? "agents.default_subagent_model" : "model",
      reasoning_effort: state.target === "subagents" ? "agents.default_subagent_reasoning_effort"
        : state.target === "role" ? "model_reasoning_effort" : "model_reasoning_effort",
      speed: "service_tier",
      model_context_window: "model_context_window",
      model_auto_compact_token_limit: "model_auto_compact_token_limit",
    };
    result.changes = resetKeys
      .map((key) => fieldByKey[key])
      .filter((field) => Object.prototype.hasOwnProperty.call(source, field))
      .map((field) => ({ setting: field, before: source[field], after: "(unset)" }));
    openReview(result, "reset", request, resetKeys);
  } catch (error) {
    openReview({ changes: [], warnings: [error.message], filesAffected: [] }, "error", request);
    setStatus(error.message, "error");
  }
}

document.querySelectorAll(".scope-tab").forEach((button) => {
  button.addEventListener("click", async () => {
    clearPendingChoices();
    state.scope = button.dataset.scope;
    document.querySelectorAll(".scope-tab").forEach((item) => {
      item.setAttribute("aria-selected", String(item === button));
    });
    renderForm();
    if (state.scope === "global" || state.projectRoot) {
      try { await loadConfig(); } catch (error) { setStatus(error.message, "error"); }
    }
  });
});

byId("target").addEventListener("change", async () => {
  clearPendingChoices();
  state.target = byId("target").value;
  renderForm();
  if (state.target === "role") {
    try { await loadConfig({ includeRoles: true }); }
    catch (error) { setStatus(error.message || t("operationFailed"), "error"); }
  }
});
byId("role-name").addEventListener("change", async () => {
  clearPendingChoices();
  renderForm();
  if (state.target === "role") {
    try { await loadConfig({ includeRoles: true }); }
    catch (error) { setStatus(error.message || t("operationFailed"), "error"); }
  }
});
byId("project-root").addEventListener("change", async (event) => {
  clearPendingChoices();
  state.projectRoot = normalizeProjectRoot(event.target.value);
  event.target.value = state.projectRoot;
  try {
    await loadConfig();
    setLocalizedStatus("projectChanged", "good");
  } catch (error) {
    setStatus(error.message, "error");
  }
});
byId("model").addEventListener("change", () => {
  const nextModel = byId("model").value;
  const previousEffort = byId("reasoning").value;
  const activeEffort = currentField(activeSettings(), "reasoning_effort");
  const effectiveEffort = currentField(effectiveSettings(), "reasoning_effort");
  state.pendingModel = nextModel;
  state.pendingReasoning = undefined;
  if (nextModel) {
    const selected = modelById(nextModel);
    const oldEffort = previousEffort || activeEffort || effectiveEffort;
    if (selected && oldEffort && !selected.reasoningEfforts.includes(oldEffort)) {
      const fallback = selected.reasoningEfforts.includes(selected.defaultReasoningEffort)
        ? selected.defaultReasoningEffort
        : selected.reasoningEfforts[0];
      state.pendingReasoning = fallback || "";
      if (fallback) setLocalizedStatus("reasoningChanged", "good");
    } else if (previousEffort || activeEffort) {
      state.pendingReasoning = previousEffort || activeEffort;
    }
  }
  renderModelOptions();
  renderContextBounds();
});
byId("reasoning").addEventListener("change", () => {
  state.pendingReasoning = byId("reasoning").value;
  syncCustomSelect("reasoning");
});
byId("preview").addEventListener("click", preview);
byId("reset").addEventListener("click", resetLayer);
byId("review-close").addEventListener("click", () => reviewDialog.close());
byId("review-cancel").addEventListener("click", () => reviewDialog.close());
byId("review-confirm").addEventListener("click", applyReviewed);
byId("help-open").addEventListener("click", () => helpDialog.showModal());
byId("help-close").addEventListener("click", () => helpDialog.close());
byId("help-done").addEventListener("click", () => helpDialog.close());
byId("roles-open").addEventListener("click", openRoleManager);
byId("roles-close").addEventListener("click", () => rolesDialog.close());
byId("roles-done").addEventListener("click", () => rolesDialog.close());
byId("roles-dialog").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-role-action]");
  if (!button) return;
  const { roleAction, roleName, roleScope } = button.dataset;
  if (roleAction === "edit") {
    await editManagedRole(roleScope, roleName);
  } else if (roleAction === "delete") {
    confirmRoleDelete(roleScope, roleName);
  }
});
byId("role-delete-close").addEventListener("click", () => roleDeleteDialog.close());
byId("role-delete-cancel").addEventListener("click", () => roleDeleteDialog.close());
byId("role-delete-confirm").addEventListener("click", deleteSelectedRole);
byId("logs-open").addEventListener("click", () => {
  helpDialog.close();
  logsDialog.showModal();
  loadPluginLogs();
});
byId("logs-close-icon").addEventListener("click", () => logsDialog.close());
byId("logs-done").addEventListener("click", () => logsDialog.close());
byId("logs-refresh").addEventListener("click", loadPluginLogs);
reviewDialog.addEventListener("click", (event) => { if (event.target === reviewDialog) reviewDialog.close(); });
helpDialog.addEventListener("click", (event) => { if (event.target === helpDialog) helpDialog.close(); });
rolesDialog.addEventListener("click", (event) => { if (event.target === rolesDialog) rolesDialog.close(); });
roleDeleteDialog.addEventListener("click", (event) => { if (event.target === roleDeleteDialog) roleDeleteDialog.close(); });
logsDialog.addEventListener("click", (event) => { if (event.target === logsDialog) logsDialog.close(); });
byId("context-window").addEventListener("input", renderContextBounds);
byId("context-window").addEventListener("change", suggestCompactLimit);
byId("compact-limit").addEventListener("input", () => {
  state.compactManuallyEdited = true;
  renderContextBounds();
});
document.querySelectorAll("[data-step-target]").forEach((button) => {
  button.addEventListener("click", () => {
    stepTokenInput(byId(button.dataset.stepTarget), Number(button.dataset.stepDirection));
  });
});
for (const id of ["context-window", "compact-limit"]) {
  const input = byId(id);
  input.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowUp" && event.key !== "ArrowDown") return;
    event.preventDefault();
    stepTokenInput(input, event.key === "ArrowUp" ? 1 : -1);
  });
  input.addEventListener("wheel", (event) => {
    if (document.activeElement !== input || event.ctrlKey || event.deltaY === 0) return;
    event.preventDefault();
    stepTokenInput(input, event.deltaY < 0 ? 1 : -1);
  }, { passive: false });
}
byId("refresh").addEventListener("click", async () => {
  try {
    setLocalizedStatus("catalogRefreshing");
    const catalog = await loadCatalog(true);
    setLocalizedStatus(catalog.warning ? "fallbackCatalog" : "catalogRefreshed", catalog.warning ? "error" : "good");
  } catch (error) {
    setStatus(error.message, "error");
  }
});

function closeCustomSelect(control) {
  control.listbox.hidden = true;
  control.trigger.setAttribute("aria-expanded", "false");
  control.trigger.removeAttribute("aria-activedescendant");
  control.activeIndex = -1;
}

function renderCustomOptions(control) {
  control.listbox.replaceChildren();
  Array.from(control.select.options).forEach((option, index) => {
    const item = document.createElement("div");
    item.id = `${control.listbox.id}-option-${index}`;
    item.className = "select-option";
    item.setAttribute("role", "option");
    item.setAttribute("aria-selected", String(option.value === control.select.value));
    item.setAttribute("aria-disabled", String(option.disabled));
    item.dataset.active = "false";
    item.textContent = option.textContent;
    item.addEventListener("pointermove", () => {
      if (!option.disabled) setActiveCustomOption(control, index);
    });
    item.addEventListener("click", () => chooseCustomOption(control, index));
    control.listbox.append(item);
  });
}

function syncCustomSelect(id) {
  const control = customSelects.get(id);
  if (!control) return;
  const options = Array.from(control.select.options);
  const selected = options.find((option) => option.value === control.select.value) || options[0];
  const value = document.createElement("span");
  value.className = "select-value";
  value.textContent = selected?.textContent || t("noModelChoice");
  const chevron = document.createElement("span");
  chevron.className = "select-chevron";
  chevron.setAttribute("aria-hidden", "true");
  control.trigger.replaceChildren(value, chevron);
  control.trigger.disabled = control.select.disabled;
  renderCustomOptions(control);
  if (!control.listbox.hidden) {
    positionCustomSelect(control);
    setActiveCustomOption(control, Math.max(0, control.activeIndex));
  }
}

function syncAllCustomSelects() {
  customSelects.forEach((_, id) => syncCustomSelect(id));
}

function positionCustomSelect(control) {
  const rect = control.trigger.getBoundingClientRect();
  const width = Math.min(rect.width, window.innerWidth - 24);
  const left = Math.max(12, Math.min(rect.left, window.innerWidth - width - 12));
  const below = window.innerHeight - rect.bottom - 12;
  const above = rect.top - 12;
  const maxHeight = Math.min(320, Math.max(112, Math.max(above, below)));
  control.listbox.style.maxHeight = `${maxHeight}px`;
  const height = Math.min(control.listbox.scrollHeight, maxHeight);
  const openAbove = below < height && above > below;
  control.listbox.style.left = `${left}px`;
  control.listbox.style.top = `${openAbove ? Math.max(12, rect.top - height - 5) : Math.min(window.innerHeight - height - 12, rect.bottom + 5)}px`;
  control.listbox.style.width = `${width}px`;
}

function setActiveCustomOption(control, index) {
  const options = Array.from(control.select.options);
  if (!options.length) return;
  const direction = index >= control.activeIndex ? 1 : -1;
  let next = Math.max(0, Math.min(options.length - 1, index));
  while (options[next]?.disabled) {
    next += direction;
    if (next < 0 || next >= options.length) return;
  }
  control.activeIndex = next;
  control.listbox.querySelectorAll('[role="option"]').forEach((item, itemIndex) => {
    item.dataset.active = String(itemIndex === next);
  });
  const active = control.listbox.children[next];
  if (active) {
    control.trigger.setAttribute("aria-activedescendant", active.id);
    active.scrollIntoView({ block: "nearest" });
  }
}

function selectedCustomOptionIndex(control) {
  const options = Array.from(control.select.options);
  const selected = options.findIndex((option) => option.value === control.select.value && !option.disabled);
  return selected >= 0 ? selected : options.findIndex((option) => !option.disabled);
}

function openCustomSelect(control) {
  if (control.select.disabled) return;
  customSelects.forEach((other) => { if (other !== control) closeCustomSelect(other); });
  renderCustomOptions(control);
  control.listbox.hidden = false;
  control.listbox.style.visibility = "hidden";
  control.trigger.setAttribute("aria-expanded", "true");
  positionCustomSelect(control);
  control.listbox.style.visibility = "";
  setActiveCustomOption(control, selectedCustomOptionIndex(control));
}

function chooseCustomOption(control, index) {
  const option = control.select.options[index];
  if (!option || option.disabled || control.select.disabled) return;
  control.select.value = option.value;
  control.select.dispatchEvent(new Event("change", { bubbles: true }));
  closeCustomSelect(control);
  control.trigger.focus();
}

function initCustomSelects() {
  document.querySelectorAll("select.custom-select-source").forEach((select) => {
    const label = document.querySelector(`label[for="${select.id}"]`);
    const shell = document.createElement("div");
    shell.className = "select-shell";
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.id = `${select.id}-combobox`;
    trigger.className = "control select-trigger";
    trigger.setAttribute("role", "combobox");
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");
    trigger.setAttribute("aria-controls", `${select.id}-listbox`);
    if (label) {
      if (!label.id) label.id = `${select.id}-label`;
      label.htmlFor = trigger.id;
      trigger.setAttribute("aria-labelledby", label.id);
    }
    const listbox = document.createElement("div");
    listbox.id = `${select.id}-listbox`;
    listbox.className = "select-popover";
    listbox.setAttribute("role", "listbox");
    if (label) listbox.setAttribute("aria-labelledby", label.id);
    listbox.hidden = true;
    shell.append(trigger);
    select.after(shell);
    document.body.append(listbox);

    const control = { select, shell, trigger, listbox, activeIndex: -1, typeahead: "", typeaheadTimer: null };
    customSelects.set(select.id, control);
    trigger.addEventListener("click", () => listbox.hidden ? openCustomSelect(control) : closeCustomSelect(control));
    trigger.addEventListener("keydown", (event) => {
      const options = Array.from(select.options);
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        if (listbox.hidden) openCustomSelect(control);
        else setActiveCustomOption(control, control.activeIndex + (event.key === "ArrowDown" ? 1 : -1));
      } else if (event.key === "Home" || event.key === "End") {
        event.preventDefault();
        if (listbox.hidden) openCustomSelect(control);
        setActiveCustomOption(control, event.key === "Home" ? 0 : options.length - 1);
      } else if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        if (listbox.hidden) openCustomSelect(control);
        else if (control.activeIndex >= 0) chooseCustomOption(control, control.activeIndex);
      } else if (event.key === "Escape" && !listbox.hidden) {
        event.preventDefault();
        closeCustomSelect(control);
      } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
        control.typeahead += event.key.toLocaleLowerCase();
        clearTimeout(control.typeaheadTimer);
        control.typeaheadTimer = setTimeout(() => { control.typeahead = ""; }, 500);
        const match = options.findIndex((option) => !option.disabled && option.textContent.toLocaleLowerCase().startsWith(control.typeahead));
        if (match >= 0) {
          if (listbox.hidden) openCustomSelect(control);
          setActiveCustomOption(control, match);
        }
      }
    });
    select.addEventListener("change", () => syncCustomSelect(select.id));
    syncCustomSelect(select.id);
  });

  document.addEventListener("pointerdown", (event) => {
    customSelects.forEach((control) => {
      if (!control.shell.contains(event.target) && !control.listbox.contains(event.target)) closeCustomSelect(control);
    });
  }, true);
  window.addEventListener("resize", () => {
    customSelects.forEach((control) => { if (!control.listbox.hidden) positionCustomSelect(control); });
  });
  window.addEventListener("scroll", () => {
    customSelects.forEach((control) => { if (!control.listbox.hidden) positionCustomSelect(control); });
  }, true);
}

function syncScopeTabs() {
  document.querySelectorAll(".scope-tab").forEach((item) => {
    item.setAttribute("aria-selected", String(item.dataset.scope === state.scope));
  });
}

function applyToolInput(input) {
  const args = input?.arguments || input?.input || input || {};
  const root = normalizeProjectRoot(args.project_root ?? args.projectRoot);
  const nextScope = root ? "project" : "global";
  const changed = root !== state.projectRoot || nextScope !== state.scope || state.target !== "subagents";
  clearPendingChoices();
  state.projectRoot = root || "";
  state.scope = nextScope;
  state.target = "subagents";
  byId("project-root").value = state.projectRoot;
  byId("target").value = state.target;
  syncScopeTabs();
  renderForm();
  if (changed && state.connected) {
    loadConfig().then(() => setLocalizedStatus(root ? "projectChanged" : "loaded", "good"))
      .catch((error) => setStatus(error.message || t("operationFailed"), "error"));
  }
}

app.ontoolinput = applyToolInput;
app.onhostcontextchanged = (context) => applyHostContext({ ...(app.getHostContext() || {}), ...context });
app.onerror = (error) => setStatus(error.message || t("operationFailed"), "error");

applyLocale();
byId("target").value = state.target;
syncScopeTabs();
renderForm();
initCustomSelects();
if (globalThis.openai?.toolInput) applyToolInput(globalThis.openai.toolInput);
await app.connect();
state.connected = true;
applyHostContext(app.getHostContext() || {});
setLocalizedStatus("loadingSettings");
let catalogState = "";
let catalogError = "";
loadCatalog(false).then((catalog) => {
  catalogState = catalog.warning ? "fallbackCatalog" : "loaded";
  if (state.configReady && !state.configFailed) setLocalizedStatus(catalogState, catalog.warning ? "warn" : "good");
}).catch((error) => {
  catalogState = "catalogFailed";
  catalogError = error.message || t("operationFailed");
  if (state.configReady && !state.configFailed) setStatus(catalogError, "error");
});
void loadConfig({ includeRoles: false }).then(() => {
  state.configReady = true;
  state.configFailed = false;
  if (catalogState === "catalogFailed") setStatus(catalogError, "error");
  else setLocalizedStatus(catalogState || "configReady", catalogState === "fallbackCatalog" ? "warn" : "good");
}).catch((error) => {
  state.configReady = true;
  state.configFailed = true;
  setStatus(error.message || t("operationFailed"), "error");
});
