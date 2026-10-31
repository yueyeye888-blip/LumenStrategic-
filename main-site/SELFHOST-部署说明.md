# LUMEN 新版官网部署说明

本次更新加入了真实的合作申请保存功能，已经不再是“只上传静态文件”就能完整运行的版本。

## 普通 Linux / 宝塔 / Nginx 服务器

页面在 website/，默认英文首页，简体中文位于 /zh-hans/，包含全部图片；繁体中文已移除；表单后台在 selfhost/，使用 Python 3.10+、Gunicorn 和 SQLite。不要将 selfhost 或数据目录设为公开网站根目录。

1. 将本包解压到 /var/www/lumen。Nginx 网站根目录指向 /var/www/lumen/website。
2. 在 selfhost/ 创建虚拟环境并安装依赖：

```bash
cd /var/www/lumen/selfhost
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo install -d -o www-data -g www-data -m 700 /var/lib/lumen
sudo -u www-data env LUMEN_DB_PATH=/var/lib/lumen/applications.sqlite3 .venv/bin/python app.py
```

3. 参考 selfhost/lumen-form.service.example 创建 systemd 服务，将 example.com 改成你的 HTTPS 域名，并按服务器实际用户调整 www-data。启动并设置开机自启。
4. 参考 selfhost/nginx.conf.example 配置网站与 /api/applications 反向代理，检查 Nginx 配置后重新加载。通过宝塔或 Certbot 为实际域名申请证书并开启 HTTPS。
5. 用测试资料提交一次，只有后台保存成功才会弹出“申请成功”。若后台未启动或写入失败，页面会显示失败提示。

申请保存在 /var/lib/lumen/applications.sqlite3，不会自动发到邮箱。需要通知邮件时另行配置邮件服务。请备份这个数据库文件；不要放到公开网页目录。

在服务器上导出申请：

```bash
cd /var/www/lumen/selfhost
sudo -u www-data env LUMEN_DB_PATH=/var/lib/lumen/applications.sqlite3 .venv/bin/python export_applications.py > applications.csv
```

导出文件包含申请人资料，请保存在管理员目录，不要放在 website/。

## 当前 Sites 在线版

在线版使用 Vinext / Cloudflare Worker 和 D1 保存申请。app/api/applications/route.ts 是接收接口，db/schema.ts 和 drizzle/ 是数据库结构与迁移。website/ 是页面源文件，build_site.py 生成两个语言版本。构建时 scripts/sync-website.mjs 同步图片、CSS 和 JavaScript。

Sites/D1 上的资料与自行部署服务器的 SQLite 数据库彼此独立，不会随代码包自动迁移。本包不含任何申请资料、账号密钥或访问令牌。

本包只包含公司官网，收益模拟器保留为现有独立网址链接。
