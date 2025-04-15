resource "kubernetes_namespace_v1" "nats" {
  metadata {
    name = "nats"
    labels = {
      spawn-cert = "cloudflare-cert"
    }
  }
}
