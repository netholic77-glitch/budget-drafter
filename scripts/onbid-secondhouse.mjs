#!/usr/bin/env node
/**
 * 온비드 세컨하우스 후보 검색기
 *
 * 공공데이터포털 "한국자산관리공사_온비드 캠코공매물건 조회서비스"(15000851)와
 * "온비드 이용기관 공매물건 조회서비스"(15000849)를 호출해
 *   - 최저입찰가 N원 이하
 *   - 단독주택 · 농가주택 등 세컨하우스 성격의 주거용 물건
 *   - 수도권에서 차로 약 2시간 안쪽 지역
 * 조건으로 걸러 CSV / JSON 으로 떨군다.
 *
 * 사용법:
 *   ONBID_SERVICE_KEY=발급받은_디코딩키 node scripts/onbid-secondhouse.mjs
 *   node scripts/onbid-secondhouse.mjs --key XXX --max-price 60000000 --pages 20
 *   node scripts/onbid-secondhouse.mjs --key XXX --raw        # 원본 응답 1페이지 덤프
 *   node scripts/onbid-secondhouse.mjs --key XXX --all-regions --include-all
 *
 * 인증키 발급: https://www.data.go.kr/data/15000851/openapi.do (무료, 즉시 승인)
 */

const HELP = `
온비드 세컨하우스 후보 검색기

  --key <서비스키>       공공데이터포털 인증키(디코딩 키). 없으면 env ONBID_SERVICE_KEY 사용
  --max-price <원>       최저입찰가 상한 (기본 60000000 = 6천만원)
  --pages <N>            서비스별 최대 조회 페이지 수 (기본 10, 페이지당 100건)
  --rows <N>             페이지당 건수 (기본 100)
  --service <이름>       kamco | usage | both (기본 both)
  --all-regions          지역 필터 해제 (전국)
  --include-all          주택 유형 필터 해제 (토지·상가 등 전부)
  --out <경로>           CSV 출력 경로 (기본 out/onbid-secondhouse.csv)
  --json                 CSV 옆에 JSON도 함께 저장
  --raw                  첫 페이지 원본 응답을 그대로 출력하고 종료 (필드명 확인용)
  --fixture <경로>       네트워크 대신 로컬 XML 파일을 읽어 처리 (오프라인 검증용)
  --insecure-http        https 실패 시 http로 재시도 (기본 켜짐, --no-insecure-http로 해제)
  --help
`;

// ── 인자 파싱 ────────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const opts = {
    key: process.env.ONBID_SERVICE_KEY || '',
    maxPrice: 60_000_000,
    pages: 10,
    rows: 100,
    service: 'both',
    allRegions: false,
    includeAll: false,
    out: 'out/onbid-secondhouse.csv',
    json: false,
    raw: false,
    fixture: '',
    insecureHttp: true,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--help' || a === '-h') opts.help = true;
    else if (a === '--key') opts.key = next();
    else if (a === '--max-price') opts.maxPrice = Number(String(next()).replace(/[_,]/g, ''));
    else if (a === '--pages') opts.pages = Number(next());
    else if (a === '--rows') opts.rows = Number(next());
    else if (a === '--service') opts.service = next();
    else if (a === '--all-regions') opts.allRegions = true;
    else if (a === '--include-all') opts.includeAll = true;
    else if (a === '--out') opts.out = next();
    else if (a === '--json') opts.json = true;
    else if (a === '--raw') opts.raw = true;
    else if (a === '--fixture') opts.fixture = next();
    else if (a === '--no-insecure-http') opts.insecureHttp = false;
    else if (a === '--insecure-http') opts.insecureHttp = true;
    else throw new Error(`알 수 없는 옵션: ${a}`);
  }
  return opts;
}

// ── 대상 서비스 ──────────────────────────────────────────────────────────────
// 엔드포인트는 공공데이터포털 활용신청 화면의 "요청주소"와 반드시 대조할 것.
// 서비스가 바뀌면 여기만 고치면 된다.
const SERVICES = {
  kamco: {
    label: '캠코 공매물건',
    portal: 'https://www.data.go.kr/data/15000851/openapi.do',
    base: 'openapi.onbid.co.kr/openapi/services/KamcoPblsalThingInquireSvc/getKamcoPbctCltrList',
  },
  usage: {
    label: '이용기관 공매물건',
    portal: 'https://www.data.go.kr/data/15000849/openapi.do',
    base: 'openapi.onbid.co.kr/openapi/services/OnbidPblsalThingInquireSvc/getUnifyUsageCltrList',
  },
};

// ── 아주 작은 XML 리더 (의존성 없이 <item> 블록만 뽑는다) ────────────────────
function stripCdata(s) {
  return s.replace(/^<!\[CDATA\[([\s\S]*?)\]\]>$/, '$1');
}
function decodeEntities(s) {
  return s
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, d) => String.fromCharCode(Number(d)))
    .replace(/&amp;/g, '&');
}
function parseItems(xml) {
  const items = [];
  const itemRe = /<item>([\s\S]*?)<\/item>/g;
  let m;
  while ((m = itemRe.exec(xml))) {
    const row = {};
    const tagRe = /<([A-Za-z0-9_:.-]+)>([\s\S]*?)<\/\1>/g;
    let t;
    while ((t = tagRe.exec(m[1]))) {
      row[t[1]] = decodeEntities(stripCdata(t[2].trim()));
    }
    items.push(row);
  }
  return items;
}
function pickTag(xml, tag) {
  const m = new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`).exec(xml);
  return m ? decodeEntities(stripCdata(m[1].trim())) : '';
}

// ── 응답 필드명이 서비스/버전마다 달라 후보군으로 관대하게 매핑한다 ──────────
const FIELD_ALIASES = {
  name: ['CLTR_NM', 'GOODS_NM', 'CLTR_NM_CTGR', 'PLNM_NM'],
  category: ['CTGR_FULL_NM', 'CTGR_NM', 'CLTR_MNMT_NO_NM', 'USE_NM'],
  addr: ['LDNM_ADRS', 'NMRD_ADRS', 'CLTR_ADRS', 'ADRS', 'LD_ADRS'],
  minBid: ['MIN_BID_PRC', 'MIN_BID_AMT', 'MIN_BID_PRICE', 'FEE_RATE_MIN_BID_PRC'],
  apprAmt: ['APSL_ASES_AVG_AMT', 'APSL_ASES_AMT', 'APRS_AMT', 'ASES_AVG_AMT'],
  failCnt: ['USCBD_CNT', 'PBCT_CNT', 'BID_CNT'],
  openDt: ['PBCT_BEGN_DTM', 'OPBD_BEGIN_DTM', 'PBCT_BEGIN_DTM', 'BID_BEGN_DTM'],
  closeDt: ['PBCT_CLS_DTM', 'OPBD_CLSG_DTM', 'PBCT_CLSG_DTM', 'BID_CLS_DTM'],
  status: ['PBCT_CLTR_STAT_NM', 'CLTR_STAT_NM', 'PBCT_STAT_NM'],
  method: ['DPSL_MTD_NM', 'DPSL_MTD_CD_NM', 'BID_MTD_NM'],
  mnmtNo: ['CLTR_MNMT_NO', 'BID_MNMT_NO', 'PLNM_NO'],
  cltrNo: ['CLTR_NO'],
  cltrHstrNo: ['CLTR_HSTR_NO'],
  plnmNo: ['PLNM_NO'],
  pbctNo: ['PBCT_NO'],
  area: ['CLTR_MNMT_NO_AREA', 'LDNM_AREA', 'BLD_AREA', 'AREA'],
};
function get(row, key) {
  for (const alias of FIELD_ALIASES[key] || []) {
    if (row[alias] != null && row[alias] !== '') return row[alias];
  }
  return '';
}
function num(v) {
  const n = Number(String(v).replace(/[^0-9.-]/g, ''));
  return Number.isFinite(n) ? n : 0;
}

// ── 수도권에서 차로 약 2시간 권역 (서울 기준, 도로 사정에 따라 가감) ─────────
// 기준: 국토교통부 도로망 기준 서울 도심 출발 승용차 2시간 내외 도달 시·군.
// 정확한 소요시간은 물건별로 반드시 재확인할 것.
const NEAR_METRO = [
  // 경기 (전역이 대체로 2시간 이내)
  '경기', '가평', '양평', '여주', '이천', '안성', '포천', '연천', '파주', '광주시', '남양주', '용인', '평택', '화성', '양주', '동두천',
  // 인천 (강화·옹진 포함)
  '인천', '강화', '옹진',
  // 강원 영서
  '춘천', '홍천', '원주', '횡성', '철원', '화천', '양구', '인제', '평창',
  // 충북 북부
  '충주', '제천', '음성', '진천', '괴산', '단양', '증평',
  // 충남 북부
  '천안', '아산', '당진', '예산', '홍성', '서산', '태안', '보령',
];
// 명백히 2시간을 넘는 지역은 지역 키워드가 스쳐도 배제한다.
const FAR_EXCLUDE = ['제주', '서귀포', '부산', '울산', '창원', '거제', '통영', '여수', '순천', '목포', '해남', '완도', '진도', '강릉', '속초', '삼척', '동해', '태백', '경주', '포항', '광양', '남해', '고흥', '장흥', '보성'];

// ── 세컨하우스 성격의 주거 물건 ──────────────────────────────────────────────
// 이 단어가 보이면 유형 판정 끝 — 세컨하우스로 쓸 수 있는 단독 형태
const HOUSE_STRONG = ['단독주택', '다가구', '농가주택', '농어촌주택', '전원주택', '별장', '농가', '주택 및 토지'];
// 강한 단서가 없을 때만 인정하는 약한 단서
const HOUSE_WEAK = ['주택', '주거용'];
// 강한 단서가 없는데 이 단어가 있으면 제외
const HOUSE_EXCLUDE = ['아파트', '오피스텔', '연립', '다세대', '상가', '점포', '공장', '창고', '근린생활', '숙박', '사무실', '지분', '차량', '기계', '선박', '회원권', '토지', '임야', '전답', '답 ', '잡종지'];

function isNearMetro(text) {
  if (!text) return false;
  if (FAR_EXCLUDE.some((k) => text.includes(k))) return false;
  return NEAR_METRO.some((k) => text.includes(k));
}
function isHouseLike(text) {
  if (!text) return false;
  if (HOUSE_STRONG.some((k) => text.includes(k))) return true;
  if (HOUSE_EXCLUDE.some((k) => text.includes(k))) return false;
  return HOUSE_WEAK.some((k) => text.includes(k));
}

// ── 호출 ────────────────────────────────────────────────────────────────────
async function fetchPage(svc, opts, pageNo) {
  if (opts.fixture) {
    if (pageNo > 1) return '<response><body><items></items><totalCount>0</totalCount></body></response>';
    const { readFileSync } = await import('node:fs');
    return readFileSync(opts.fixture, 'utf-8');
  }
  const qs = new URLSearchParams({
    serviceKey: opts.key,
    numOfRows: String(opts.rows),
    pageNo: String(pageNo),
  });
  const attempts = [`https://${svc.base}?${qs}`];
  if (opts.insecureHttp) attempts.push(`http://${svc.base}?${qs}`);

  let lastErr;
  for (const url of attempts) {
    try {
      const res = await fetch(url, { headers: { Accept: 'application/xml' }, signal: AbortSignal.timeout(30_000) });
      const body = await res.text();
      if (!res.ok) throw new Error(`HTTP ${res.status} — ${body.slice(0, 300)}`);
      return body;
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr;
}

function checkServiceError(xml, svc) {
  const code = pickTag(xml, 'resultCode') || pickTag(xml, 'returnReasonCode');
  const msg = pickTag(xml, 'resultMsg') || pickTag(xml, 'returnAuthMsg') || pickTag(xml, 'errMsg');
  if (code && !['00', '0', '000'].includes(code)) {
    throw new Error(`[${svc.label}] 서비스 오류 ${code}: ${msg}\n  → 인증키 승인 여부와 요청주소를 ${svc.portal} 에서 확인하세요.`);
  }
}

async function collect(svc, opts) {
  const rows = [];
  for (let page = 1; page <= opts.pages; page++) {
    const xml = await fetchPage(svc, opts, page);
    if (opts.raw) {
      console.log(`\n===== ${svc.label} raw page ${page} =====\n`);
      console.log(xml.slice(0, 8000));
      return rows;
    }
    checkServiceError(xml, svc);
    const items = parseItems(xml);
    rows.push(...items.map((r) => ({ ...r, __source: svc.label })));
    const total = num(pickTag(xml, 'totalCount'));
    process.stderr.write(`  ${svc.label} page ${page}: ${items.length}건 (누적 ${rows.length}${total ? ` / 전체 ${total}` : ''})\n`);
    if (items.length < opts.rows) break;
    if (total && rows.length >= total) break;
  }
  return rows;
}

// ── 정리 ────────────────────────────────────────────────────────────────────
function normalize(raw) {
  const name = get(raw, 'name');
  const category = get(raw, 'category');
  const addr = get(raw, 'addr');
  const minBid = num(get(raw, 'minBid'));
  const appraised = num(get(raw, 'apprAmt'));
  return {
    source: raw.__source,
    name,
    category,
    addr,
    minBid,
    appraised,
    // 감정가 대비 최저입찰가 비율 — 낮을수록 유찰이 누적돼 값이 빠진 물건
    priceRatio: appraised > 0 ? Math.round((minBid / appraised) * 1000) / 10 : null,
    failCnt: num(get(raw, 'failCnt')),
    status: get(raw, 'status'),
    method: get(raw, 'method'),
    openDt: get(raw, 'openDt'),
    closeDt: get(raw, 'closeDt'),
    mnmtNo: get(raw, 'mnmtNo'),
    link: buildLink(raw),
    haystack: [name, category, addr].join(' '),
  };
}
function buildLink(raw) {
  const cltrHstrNo = get(raw, 'cltrHstrNo');
  const cltrNo = get(raw, 'cltrNo');
  const plnmNo = get(raw, 'plnmNo');
  const pbctNo = get(raw, 'pbctNo');
  if (cltrHstrNo && cltrNo && plnmNo && pbctNo) {
    return `https://www.onbid.co.kr/op/cta/cltrdtl/collateralRealEstateDetail.do?cltrHstrNo=${cltrHstrNo}&cltrNo=${cltrNo}&plnmNo=${plnmNo}&pbctNo=${pbctNo}`;
  }
  return 'https://www.onbid.co.kr';
}

function toCsv(rows) {
  const cols = ['순위', '물건명', '용도', '소재지', '최저입찰가(원)', '감정가(원)', '감정가대비(%)', '유찰횟수', '입찰기간', '처분방식', '상태', '관리번호', '출처', '상세링크'];
  const esc = (v) => {
    const s = v == null ? '' : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [cols.join(',')];
  rows.forEach((r, i) => {
    lines.push([
      i + 1, r.name, r.category, r.addr, r.minBid, r.appraised || '',
      r.priceRatio ?? '', r.failCnt || '', [r.openDt, r.closeDt].filter(Boolean).join('~'),
      r.method, r.status, r.mnmtNo, r.source, r.link,
    ].map(esc).join(','));
  });
  return '﻿' + lines.join('\n') + '\n'; // 엑셀 한글 깨짐 방지용 BOM
}

const won = (n) => (n ? `${(n / 10_000).toLocaleString('ko-KR')}만원` : '-');

// ── main ────────────────────────────────────────────────────────────────────
async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) return console.log(HELP);
  if (!opts.key && !opts.fixture) {
    console.error('인증키가 없습니다. --key 또는 환경변수 ONBID_SERVICE_KEY 를 지정하세요.');
    console.error('발급: https://www.data.go.kr/data/15000851/openapi.do (무료·즉시)');
    process.exit(1);
  }

  const targets = opts.service === 'both' ? ['kamco', 'usage'] : [opts.service];
  const raws = [];
  for (const key of targets) {
    const svc = SERVICES[key];
    if (!svc) throw new Error(`알 수 없는 서비스: ${key}`);
    process.stderr.write(`▸ ${svc.label} 조회 중…\n`);
    try {
      raws.push(...(await collect(svc, opts)));
    } catch (err) {
      console.error(`  ✗ ${svc.label} 실패: ${err.message}`);
    }
  }
  if (opts.raw) return;

  process.stderr.write(`\n수집 ${raws.length}건 → 필터링\n`);

  const all = raws.map(normalize);
  const filtered = all
    .filter((r) => r.minBid > 0 && r.minBid <= opts.maxPrice)
    .filter((r) => opts.includeAll || isHouseLike(r.haystack))
    .filter((r) => opts.allRegions || isNearMetro(r.addr || r.haystack))
    // 감정가 대비 싸게 나온 순 → 같으면 최저입찰가 낮은 순
    .sort((a, b) => (a.priceRatio ?? 999) - (b.priceRatio ?? 999) || a.minBid - b.minBid);

  const fs = await import('node:fs');
  const path = await import('node:path');
  fs.mkdirSync(path.dirname(opts.out), { recursive: true });
  fs.writeFileSync(opts.out, toCsv(filtered));
  if (opts.json) {
    const jsonPath = opts.out.replace(/\.csv$/, '') + '.json';
    fs.writeFileSync(jsonPath, JSON.stringify(filtered, null, 2));
    process.stderr.write(`JSON 저장: ${jsonPath}\n`);
  }

  console.log(`\n조건: 최저입찰가 ${won(opts.maxPrice)} 이하 / ${opts.includeAll ? '전 유형' : '단독·농가주택 위주'} / ${opts.allRegions ? '전국' : '수도권 차로 2시간권'}`);
  console.log(`결과: ${filtered.length}건 (수집 ${all.length}건 중)\n`);
  filtered.slice(0, 20).forEach((r, i) => {
    console.log(`${String(i + 1).padStart(2)}. ${r.name || '(물건명 없음)'}`);
    console.log(`    ${r.addr || '주소 미상'}`);
    console.log(`    최저 ${won(r.minBid)}${r.appraised ? ` / 감정 ${won(r.appraised)} (${r.priceRatio}%)` : ''}${r.failCnt ? ` · 유찰 ${r.failCnt}회` : ''}`);
    console.log(`    ${[r.openDt, r.closeDt].filter(Boolean).join(' ~ ') || '입찰기간 미상'} · ${r.link}`);
  });
  if (filtered.length > 20) console.log(`\n… 외 ${filtered.length - 20}건은 CSV 참고`);
  console.log(`\nCSV 저장: ${opts.out}`);
  console.log('※ 최저입찰가는 회차마다 바뀝니다. 입찰 전 온비드 물건상세와 등기부·현황조사서를 반드시 직접 확인하세요.');
}

main().catch((err) => {
  console.error(`\n오류: ${err.message}`);
  process.exit(1);
});
