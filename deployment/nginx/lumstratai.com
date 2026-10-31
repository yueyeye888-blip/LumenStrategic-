server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name lumstratai.com;

    root /var/www/lumen-simulator/current/dist;
    index index.html;
    charset utf-8;

    ssl_certificate /etc/letsencrypt/live/lumstratai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lumstratai.com/privkey.pem;

    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

    location / {
        try_files $uri $uri/ =404;
    }

    location ~ /\.(?!well-known) {
        deny all;
    }

    location ~* \.(?:css|js|png|jpg|jpeg|webp|svg)$ {
        expires 1h;
        add_header Cache-Control "public";
        add_header X-Content-Type-Options "nosniff" always;
        try_files $uri =404;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name www.lumstratai.com;

    ssl_certificate /etc/letsencrypt/live/lumstratai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lumstratai.com/privkey.pem;

    return 301 https://lumstratai.com$request_uri;
}

server {
    listen 80;
    listen [::]:80;
    server_name lumstratai.com www.lumstratai.com;

    return 301 https://lumstratai.com$request_uri;
}
