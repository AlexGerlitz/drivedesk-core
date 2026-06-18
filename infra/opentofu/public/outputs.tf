output "drivedesk_public_iac_contract" {
  description = "Public-safe DriveDesk infrastructure contract summary."
  sensitive   = false
  value = {
    project            = local.project
    selected_environment = var.environment
    data_profile       = var.data_profile
    environments       = local.environments
    components         = local.components
    state_boundary     = local.state_boundary
    execution_boundary = local.execution_boundary
  }
}
