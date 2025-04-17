module "alloy" {
  source     = "./modules/alloy"
  depends_on = [module.external_secrets]
}
