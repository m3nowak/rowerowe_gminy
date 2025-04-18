terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.36.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "2.17.0"
    }
  }
}
provider "kubernetes" {
  config_path = "${path.root}/kubeconfig.yaml"

}

provider "helm" {
  kubernetes {
    config_path = "${path.root}/kubeconfig.yaml"
  }

}
