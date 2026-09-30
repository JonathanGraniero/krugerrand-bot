terraform {
  required_version = ">= 1.10"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.26"
    }
  }

  # State lives in a Cloudflare R2 bucket through R2's S3-compatible API.
  # It shares the NHL Trade Tracker's state bucket (and R2 token) under its own
  # key. The endpoint and credentials are passed at init time, see README "Deploy".
  backend "s3" {
    bucket       = "nhl-trade-tracker-tfstate"
    key          = "krugerrand-bot/terraform.tfstate"
    region       = "auto"
    use_lockfile = true

    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
    use_path_style              = true
  }
}

# Reads CLOUDFLARE_API_TOKEN from the environment.
provider "cloudflare" {}
