resource "cloudflare_workers_script" "bot" {
  account_id         = var.account_id
  script_name        = var.worker_name
  main_module        = "index.js"
  content_file       = var.worker_bundle
  content_sha256     = filesha256(var.worker_bundle)
  compatibility_date = var.compatibility_date

  bindings = concat(
    [
      {
        name = "DISCORD_APPLICATION_ID"
        type = "plain_text"
        text = var.discord_application_id
      },
      {
        name = "DISCORD_PUBLIC_KEY"
        type = "plain_text"
        text = var.discord_public_key
      },
    ],
    # Optional: without it /krugerrandfact uses the built-in facts.
    var.huggingface_api_key == "" ? [] : [
      {
        name = "HUGGINGFACE_API_KEY"
        type = "secret_text"
        text = var.huggingface_api_key
      },
    ],
  )

  observability = {
    enabled = true
    logs = {
      enabled         = true
      invocation_logs = true
    }
  }
}

resource "cloudflare_workers_script_subdomain" "bot" {
  account_id  = var.account_id
  script_name = cloudflare_workers_script.bot.script_name
  enabled     = true
}
