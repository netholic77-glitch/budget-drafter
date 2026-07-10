import "./globals.css";

export const metadata = {
  title: "예산분석지원 시스템",
  description: "엑셀/PDF 예산 자료를 업로드해 전년 대비 증감 분석과 보고서를 자동으로 생성합니다.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
