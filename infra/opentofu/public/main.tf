terraform {
  required_version = ">= 1.6.0"
}

locals {
  project = "drivedesk-core"

  environments = [
    "build",
    "staging",
    "canary",
    "production",
  ]

  components = {
    network_boundary = {
      purpose      = "separate public ingress from private runtime surfaces"
      data_profile = "non_pii_metadata"
    }
    kubernetes_runtime = {
      purpose      = "run API, worker, migrations, and platform jobs"
      data_profile = "synthetic_public_contract"
    }
    gitops_controller = {
      purpose      = "sync Helm desired state through reviewed changes"
      data_profile = "non_pii_metadata"
    }
    observability = {
      purpose      = "collect metrics, logs, alerts, and release evidence"
      data_profile = "aggregate_non_pii"
    }
    backup_storage = {
      purpose      = "hold encrypted backups in real deployments"
      data_profile = "public_contract_only"
    }
    secrets_boundary = {
      purpose      = "reference external secret managers without storing secrets"
      data_profile = "secret_values_excluded"
    }
  }

  state_boundary = {
    encrypted_state_required       = true
    locking_required               = true
    public_backend_config_included = false
    secrets_in_state_allowed       = false
  }

  execution_boundary = {
    plan_only                = true
    apply_from_public_export = false
    production_data_touched  = false
  }
}
