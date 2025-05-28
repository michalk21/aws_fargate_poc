
resource "aws_db_subnet_group" "main" {
  name       = "main-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "main-db-subnet-group"
  }
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name_prefix = "main-rds-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  tags = {
    Name = "main-rds-sg"
  }
}

resource "aws_db_instance" "main" {
  identifier             = "${var.app_name}-db"
  allocated_storage      = 20
  storage_type           = "gp3"
  engine                 = "postgres"
  engine_version         = "17.2"
  instance_class         = "db.t4g.micro"
  db_name                = "${replace(var.app_name, "-", "_")}_db"
  username               = "foo"
  password               = var.db_password
  skip_final_snapshot    = true
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  tags = {
    Name = "main-db"
  }
}
