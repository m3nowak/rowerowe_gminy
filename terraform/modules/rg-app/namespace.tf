resource "kubernetes_namespace_v1" "rg_app" {
  metadata {
    name = "rg-app"
    labels = {
      spawn-cert = "cloudflare-cert"
    }
  }
}
