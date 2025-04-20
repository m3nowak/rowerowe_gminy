module "rg_app" {
  source        = "./modules/rg-app"
  client_id     = var.client_id
  image_version = var.image_version
  generation    = 5
  depends_on    = [module.alloy, module.cert, module.postgres, module.nats, module.traefik]
}
