module "wha" {
  source        = "./modules/wha"
  client_id     = var.client_id
  image_version = var.image_version
  generation    = 15
  depends_on    = [module.alloy, module.cert, module.traefik]
}
