output "worker_url" {
  value = "https://${var.worker_name}.${var.workers_subdomain}.workers.dev"
}

output "interactions_endpoint_url" {
  description = "The Discord application's Interactions Endpoint URL. CI sets it after each deploy."
  value       = "https://${var.worker_name}.${var.workers_subdomain}.workers.dev/interactions"
}
