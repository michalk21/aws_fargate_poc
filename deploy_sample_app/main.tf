terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.6.0"
    }
  }
}

provider "docker" {
  registry_auth {
    address  = "index.docker.io"
    username = var.docker_username
    password = var.docker_password
  }
}

variable "docker_username" {
  description = "Docker Hub username"
  type        = string
}

variable "docker_password" {
  description = "Docker Hub password or token"
  type        = string
  sensitive   = true
}

variable "image_name" {
  default = "sample_rest_app"
}

variable "image_tag" {
  default = "latest"
}

resource "docker_image" "python_app" {
  name = "index.docker.io/${var.docker_username}/${var.image_name}:${var.image_tag}"
  build {
    context    = "${path.module}/sample_rest_app"
    #dockerfile = "${path.module}/sample_rest_app/Dockerfile"
  }
    triggers = {
    dir_sha1 = sha1(join("", [for f in fileset(path.module, "sample_rest_app/**") : filesha1(f)]))
  }
}

resource "docker_registry_image" "python_app_push" {
  name = docker_image.python_app.name
}
