terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
    hetznerdns = {
      source  = "timohirt/hetznerdns"
      version = "2.2.0"
    }
  }
  required_version = ">= 0.13"
}

provider "aws" {
  region = var.aws_region
}

provider "hetznerdns" {
  apitoken = var.hetzner_dns_token
}

variable "hetzner_dns_token" {
  description = "Hetzner DNS API token"
  type        = string
}

resource "aws_route53_zone" "this" {
  name    = var.domain_name
  comment = "Managed by Terraform"
}

data "hetznerdns_zone" "zone" {
  name = "flowoo.pl"
}

locals {
  name_server_map = {
    ns1 = "${aws_route53_zone.this.name_servers[0]}."
    ns2 = "${aws_route53_zone.this.name_servers[1]}."
    ns3 = "${aws_route53_zone.this.name_servers[2]}."
    ns4 = "${aws_route53_zone.this.name_servers[3]}."
  }
}

resource "hetznerdns_record" "cns" {
  for_each = local.name_server_map
  zone_id  = data.hetznerdns_zone.zone.id
  name     = "aws"
  type     = "NS"
  ttl      = 3600
  value    = each.value

}
