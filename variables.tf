
variable "aws_region" {
  default     = "eu-central-1"
  description = "AWS region where app will be deployed"
  type        = string
}
variable "app_docker_image" {
  default     = "jmalloc/echo-server"
  description = "Docker image for app"
  type        = string
}

variable "app_access_ips" {
  default     = ["75.2.60.0/24"]
  description = "IP addresses allowed to access the app"
  type        = list(string)
}

variable "app_name" {
  default     = "sample-rest-app"
  description = "App name"
  type        = string
  
}

variable "db_password" {
  default     = "password123"
  description = "Database password"
  type        = string
  
}

variable "domain_name" {
  type    = string
  default = ""
  description = "Domain name for Route 53 hosted zone and app load balancer"
  validation {
    condition     = can(regex("^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?[.])+[a-zA-Z]{2,}$", var.domain_name))
    error_message = "Domain name must be a valid domain format (supports subdomains)."
  }
}

variable aws_route53_zone_id {
  type    = string
  default = ""
  description = "AWS Route 53 hosted zone ID"
}