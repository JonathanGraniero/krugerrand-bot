variable "account_id" {
  description = "Cloudflare account ID."
  type        = string
}

variable "worker_name" {
  description = "Worker script name. Also the workers.dev hostname prefix."
  type        = string
  default     = "krugerrand-bot"
}

variable "workers_subdomain" {
  description = "The account's workers.dev subdomain (Workers & Pages → Settings in the dashboard)."
  type        = string
  default     = "graniero-jonathan"
}

variable "compatibility_date" {
  description = "Workers runtime compatibility date. Keep in sync with wrangler.toml (used by wrangler dev)."
  type        = string
  default     = "2025-09-01"
}

variable "worker_bundle" {
  description = "Path to the bundled Worker, produced by: npm run build"
  type        = string
  default     = "../dist/index.js"
}

variable "discord_application_id" {
  type = string
}

variable "discord_public_key" {
  type = string
}

variable "huggingface_api_key" {
  description = "Hugging Face token for AI-generated facts. Leave empty to use only the built-in facts."
  type        = string
  default     = ""
  sensitive   = true
}
