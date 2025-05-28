


# output "database_endpoint" {
#  description = "RDS instance endpoint"
#  value       = aws_db_instance.main.endpoint
#}


output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}
