terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.36.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "3.0.0-pre2"
    }
  }
}
provider "kubernetes" {
  config_path = "${path.root}/kubeconfig.yaml"
}

provider "helm" {
  kubernetes = {
    load_config_file = false
    config_path = "${path.root}/kubeconfig.yaml"
  }
  
}

module "migrated_example" {
  source = "./migrated-example"
  providers = {
    kubernetes = kubernetes
  }
  content = "hello world!"
  
}