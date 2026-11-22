# Kho Phôi Thiết Kế Giao Diện Chuẩn (`assets/component_blueprints.md` v1.3)

## 1. Blueprint CSS Dàn Trang Ấn Phẩm PDF A4 Nén `80%-90% Key & Mệnh Đề Cốt Lõi` (`WeasyPrint Paged Media`)

```css
@page {
  size: A4 portrait;
  margin: 18mm 16mm 18mm 16mm;
  @bottom-right {
    content: "Trang " counter(page) " / " counter(pages);
    font-size: 9pt;
    color: #334155;
  }
}

:root {
  --surface-page: #FFFFFF;
  --surface-container: #EBF5FB;
  --text-primary: #111111;
  --text-secondary: #334155;
  --structural-navy: #1E3A5F;
  --border-subtle: #CBD5E1;
  --accent-danger: #B91C1C;
  --accent-success: #047857;
  --accent-caution: #B45309;
}

body {
  font-family: "Inter", "Roboto", "DejaVu Sans", sans-serif;
  font-size: 12pt;
  line-height: 1.55;
  color: var(--text-primary);
  background-color: var(--surface-page);
}

h1, h2, h3 {
  color: var(--structural-navy);
  break-after: avoid;
  page-break-after: avoid;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 10.5pt;
  line-height: 1.35;
  margin: 10px 0 14px 0;
}

thead {
  display: table-header-group;
  background-color: var(--structural-navy);
  color: #FFFFFF;
}

tr, .flowchart-box, .clinical-callout {
  break-inside: avoid;
  page-break-inside: avoid;
}
```

## 2. Blueprint Vi Tương Tác HTML5: Nút Tải Trực Tiếp Bảo Toàn Khoảng Trắng (`Blob Download`) & Cân Bằng Nút Đáp Án `.option` (`FB-07`, `FB-24`, `FB-30`, `FB-32`)

```html
<!-- Nút tải file trực tiếp giữ nguyên khoảng trắng tên file (FB-07, FB-24) -->
<button id="btn-direct-download" class="ui-download-btn" type="button" onclick="triggerCleanFilenameDownload()">
  ⬇ Tải file
</button>

<script>
function triggerCleanFilenameDownload() {
  const exactFilename = document.documentElement.getAttribute("data-export-filename") || document.title + ".html";
  const htmlContent = "<!DOCTYPE html>\n" + document.documentElement.outerHTML;
  const blob = new Blob([htmlContent], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = exactFilename.replace(/_/g, " ");
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 200);
}
</script>
```

## 3. Quy Chuẩn Khung Lưu Đồ Tổng Kết Python (`PIL` `W = 1150px` & `SVG`)

- **Kích thước chuẩn:** Chiều rộng cố định `W = 1150px`, nền hộp chính `#EBF5FB`, viền `#1E3A5F` (`2px`), chữ đen thuần `#111111` cỡ lớn (`>= 20px` trên canvas `1150px`).
- **Bố cục:** Luôn đặt ở phần cuối bài giảng cùng với **Bảng tổng hợp các số liệu/mốc quan trọng** (`FB-21`).
