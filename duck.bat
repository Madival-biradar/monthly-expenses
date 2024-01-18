@echo off
docker-compose build
docker-compose up -d state-candidate-register
docker logs -f state-candidate-register-tnt