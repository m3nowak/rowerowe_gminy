module "external_secrets" {
  source              = "./modules/external_secrets"
  css_accessId        = var.es_access_id
  css_accessType      = var.es_access_type
  css_accessTypeParam = var.es_access_type_param
}
