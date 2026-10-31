server {
    server_name lumstrat.com www.lumstrat.com;
    root /var/www/lumen/current/website;
    index index.html;
    charset utf-8;
    client_max_body_size 20k;

    if ($host = www.lumstrat.com) {
        return 301 https://lumstrat.com$request_uri;
    }

    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    location = /api/applications {
        limit_req zone=lumen_form burst=3 nodelay;
        limit_req_status 429;
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 3s;
        proxy_read_timeout 20s;
        add_header Cache-Control "no-store" always;
    }

    location = /admin {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 3s;
        proxy_read_timeout 30s;
        add_header Cache-Control "no-store" always;
    }

    location ^~ /admin/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 3s;
        proxy_read_timeout 30s;
        add_header Cache-Control "no-store" always;
    }

    location = /en { return 301 /; }
    location = /en/ { return 301 /; }
    location = /zh-hant { return 301 /zh-hans/; }
    location = /zh-hant/ { return 301 /zh-hans/; }

    location / {
        try_files $uri $uri/ =404;
    }

    location ~ /\.(?!well-known) {
        deny all;
    }

    location ~* \.(?:css|js|webp|png|jpg|jpeg|svg)$ {
        expires 1h;
        add_header Cache-Control "public";
        add_header X-Content-Type-Options "nosniff" always;
        try_files $uri =404;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/lumstrat.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lumstrat.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}
server {
    listen 80;
    listen [::]:80;
    server_name lumstrat.com www.lumstrat.com;
    return 301 https://lumstrat.com$request_uri;
}
