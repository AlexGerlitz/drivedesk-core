variable "environment" {
  type        = string
  description = "Public-safe environment name used for the synthetic plan contract."
  default     = "staging"

  validation {
    condition     = contains(["build", "staging", "canary", "production"], var.environment)
    error_message = "Environment must be build, staging, canary, or production."
  }
}

variable "data_profile" {
  type        = string
  description = "Data profile expected by the public-safe plan contract."
  default     = "synthetic_fake_data"

  validation {
    condition     = var.data_profile == "synthetic_fake_data"
    error_message = "The public plan contract only supports synthetic_fake_data."
  }
}
