import { fileURLToPath } from "url";
import { dirname } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));

const repoName = "budget-drafter";
const isProd = process.env.NODE_ENV === "production";

/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: { root: __dirname },
  output: "export",
  basePath: isProd ? `/${repoName}` : "",
  assetPrefix: isProd ? `/${repoName}/` : "",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
