resource "kubernetes_namespace_v1" "wha" {
  metadata {
    name = "wha"
    labels = {
      spawn-cert = "cloudflare-cert"
    }
  }
}
