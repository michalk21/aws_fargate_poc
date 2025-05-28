
data "aws_route53_zone" "domain" {
   zone_id = var.aws_route53_zone_id
 }

locals {
  zone_exists = length(data.aws_route53_zone.domain) > 0
}

resource "aws_route53_record" "main" {
  count = local.zone_exists ? 1 : 0
  allow_overwrite = true
  name            = tolist(aws_acm_certificate.main.domain_validation_options)[0].resource_record_name
  records         = [tolist(aws_acm_certificate.main.domain_validation_options)[0].resource_record_value]
  type            = tolist(aws_acm_certificate.main.domain_validation_options)[0].resource_record_type
  zone_id         = data.aws_route53_zone.domain.zone_id
  ttl             = 60

}

resource "aws_route53_record" "alb" {
  count = local.zone_exists ? 1 : 0
  zone_id = data.aws_route53_zone.domain.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = false
  }
}