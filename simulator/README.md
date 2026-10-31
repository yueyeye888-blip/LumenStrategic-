# LUMEN 投资收益模拟器

HTML、CSS 与 JavaScript 静态网页，无数据库及后端依赖。

## 部署

将 dist/ 内的全部文件上传到 Nginx 或其他静态网站根目录，保留 index.html、calculator.js 和 export-image.js 的相对位置。配置域名与 HTTPS 后即可访问。

## 当前规则

约定分配基准固定为8%，Carry起征门槛同步固定8%，整体年度收益率严格超过8%才计提。页面保留认购金额和年度收益率两条滑轨。2%前置管理费、优先劣后分配、20%/30% Carry及冲回计算沿用现有逻辑。

底部说明、复制文本与下载图片已按最新要求同步更新。

## 校验

使用 Node.js 运行 node test.cjs，可校验603个金额与收益率组合以及指定收益情景、Carry边界、资金守恒和固定基准校验。

## 中英文切换

右上角语言菜单支持简体中文与English。中文主页为 dist/index.html；英文主页为 dist/en/index.html。切换时保留认购金额与年度收益率，复制内容和结果图片跟随所选语言。部署时必须完整上传 dist，包括 en 文件夹与 export-image-en.js。

source/index.html 与 source/export-image.js 为中文源模板；translations.json 保存英文术语；运行 python3 build_languages.py 重新生成两个版本。运行 node test-languages.cjs 核对中英文场景结果一致。
