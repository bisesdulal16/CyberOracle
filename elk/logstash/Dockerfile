FROM docker.elastic.co/logstash/logstash:8.13.0

# Download PostgreSQL JDBC driver so Logstash can poll the logs table
RUN curl -L -o /usr/share/logstash/logstash-core/lib/jars/postgresql.jar \
    https://jdbc.postgresql.org/download/postgresql-42.7.3.jar
