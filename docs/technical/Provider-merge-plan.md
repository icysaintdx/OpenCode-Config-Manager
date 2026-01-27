# Provider Page Merge Implementation Plan

## Document Info
- Date: 2026-01-27
- File: D:\opcdcfg\opencode_config_manager_fluent.py
- Lines: 6379-8879 (approx 2500 lines)
- Type: Major Refactoring - UI Merge

## Background

### Current State
- **ProviderPage** (lines 6379-7446): Custom Provider management, ~1067 lines
- **NativeProviderPage** (lines 7447-8879): Native Provider management, ~1432 lines
- Two independent pages, occupying two navigation menu entries

### Merge Goals
- Merge two pages into unified ProviderPage
- Use Pivot tabs to switch between custom/native providers
- Preserve all existing functionality
- Optimize navigation menu

### Reference Implementation
- **PluginPage** (line 19802): Successfully merged plugin management and Oh My OpenCode
- Uses Pivot + QStackedWidget pattern
- Each tab content created in separate _create_xxx_widget() method

## Architecture Design

### Class Structure



### Method Naming Rules

| Function | Custom Provider | Native Provider |
|----------|----------------|-----------------|
| Data Load | _load_custom_data() | _load_native_data() |
| Add | _on_custom_add() | - |
| Edit | _on_custom_edit() | - |
| Delete | _on_custom_delete() | _on_native_delete() |
| Config | - | _on_native_config() |
| Test | - | _on_native_test() |
| Fetch Models | _on_custom_fetch_models() | - |
| Query Balance | _on_custom_query_balance() | _on_native_query_balance() |

## Implementation Steps

### Step 1: Modify __init__ Method

Add AuthManager and EnvVarDetector initialization.



### Step 2: Rewrite _setup_ui Method

Create Pivot + QStackedWidget structure.



### Step 3: Create Custom Provider Tab

Implement _create_custom_provider_widget() with toolbar and table.

### Step 4: Create Native Provider Tab

Implement _create_native_provider_widget() with toolbar and table.

### Step 5: Rename Custom Provider Methods

Add custom_ prefix to all ProviderPage methods.

### Step 6: Rename Native Provider Methods

Add native_ prefix to all NativeProviderPage methods.

### Step 7: Update Translations

Add to locales/zh_CN.json and locales/en_US.json:


### Step 8: Update Navigation Menu

Remove NativeProviderPage registration from _init_navigation().

## Testing Checklist

- [ ] Custom Provider: Add/Edit/Delete
- [ ] Custom Provider: Fetch Models/Query Balance
- [ ] Native Provider: Config/Test/Delete
- [ ] Native Provider: Detect Configured/Query Balance
- [ ] Tab switching works correctly
- [ ] Both tabs refresh on config change

## Key Points

1. **Variable References**: Update all self.table to self.custom_table or self.native_table
2. **Keep NativeProviderPage Class**: Do not delete original class definition
3. **ModelFetchService**: Preserve for custom provider model fetching
4. **Dialog References**: ProviderDialog, NativeProviderDialog remain unchanged
5. **Signal Connections**: Ensure all button signals connect to correct methods

## Estimated Impact

- Lines to modify: ~2500
- New methods: 2 (_create_custom_provider_widget, _create_native_provider_widget)
- Methods to rename: ~30
- Translation keys to add: 2

