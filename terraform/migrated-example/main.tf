terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.36.0"
    }
  }
}

variable "content" {
  type = string
}



resource "kubernetes_namespace_v1" "migrated_ns" {
  metadata {
    name = "tf-migration-test"
  }
}

resource "kubernetes_manifest" "migrated_cfg" {
  manifest = yamldecode(file("${path.module}/cfg.yaml"))
}
