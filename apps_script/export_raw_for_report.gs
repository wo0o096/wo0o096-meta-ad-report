/**
 * 주간 소재 성과보고서용 Google raw 내보내기 (REPORT_SPEC.md §1, §10)
 *
 * 설치: 스프레드시트 「구글 애즈 소재분석 raw 정제작업」 > 확장 프로그램 > Apps Script 에
 * 이 파일 내용을 붙여넣고, installTrigger() 를 한 번 실행한다 (매주 월 07시 KST 자동 실행).
 * 수동 실행: exportRawForReport()
 *
 * 결과: 내 드라이브 / report_export / report_export_<게임>.csv (매주 같은 파일을 덮어씀)
 */

const EXPORT_GAMES = ['갓슬레이어', '이블헌터', '소마스', '언더다크', '던전견문록', '위키드'];
const EXPORT_FOLDER_NAME = 'report_export';
const EXPORT_HEADER = ['os', 'type', 'prereg', 'creative', 'cost', 'impressions', 'installs', 'conv_value', 'conversions', 'rows'];

// raw_* 열 위치 (0-based): A 캠페인, C 앱 확장 소재, D 유형, F 비용, G 노출, I 설치, K 전환 가치, L 전환, M Creative Name
const COL = { campaign: 0, asset: 2, assetType: 3, cost: 5, impressions: 6, installs: 8, convValue: 10, conversions: 11, creative: 12 };

function exportRawForReport() {
  const ss = SpreadsheetApp.getActiveSpreadsheet() || SpreadsheetApp.openById('1HrHAnEilvRWbxO6CITQeFOhbLqVBfqzBf8bsxJuo-KI');
  const folder = getOrCreateFolder_(EXPORT_FOLDER_NAME);
  const summary = [];
  EXPORT_GAMES.forEach(function (game) {
    const sheet = ss.getSheetByName('raw_' + game);
    if (!sheet) {
      summary.push(game + ': 탭 없음');
      return;
    }
    const lastRow = sheet.getLastRow();
    const values = lastRow >= 2 ? sheet.getRange(2, 1, lastRow - 1, 13).getValues() : [];
    const rows = aggregateRawRows(values);
    writeCsv_(folder, 'report_export_' + game + '.csv', toCsv([EXPORT_HEADER].concat(rows)));
    summary.push(game + ': ' + rows.length + '개 소재');
  });
  Logger.log(summary.join('\n'));
}

function installTrigger() {
  ScriptApp.getProjectTriggers()
    .filter(function (t) { return t.getHandlerFunction() === 'exportRawForReport'; })
    .forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('exportRawForReport')
    .timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(7).inTimezone('Asia/Seoul')
    .create();
}

// ---- 순수 로직 (Node 테스트 대상) ----

function toNumber(v) {
  if (typeof v === 'number') return isFinite(v) ? v : 0;
  const n = parseFloat(String(v == null ? '' : v).replace(/[^0-9.\-]/g, ''));
  return isFinite(n) ? n : 0;
}

function classifyType(assetType) {
  const t = String(assetType || '').trim();
  if (t === 'YouTube 동영상') return '영상';
  if (/이미지$/.test(t)) return '이미지';
  return null;
}

function detectOs(campaign) {
  const m = String(campaign || '').match(/(?:^|_)(iOS|AOS)(?:_|$)/i);
  if (!m) return '기타';
  return m[1].toUpperCase() === 'IOS' ? 'iOS' : 'AOS';
}

// REPORT_SPEC §2 소재명 정제
function cleanCreativeName(creative, asset) {
  let name = String(creative == null ? '' : creative);
  if (!name.trim() || /^#(VALUE|REF|N\/A|ERROR|NAME)/.test(name.trim())) {
    name = String(asset == null ? '' : asset).split(';')[0];
  }
  name = name.replace(/[\r\n]+/g, ' ');
  name = name.replace(/^\s*\d+(-\d+)?\.\s*/, '');
  name = name.replace(/_\d+x\d+\.(jpg|jpeg|png|gif)$/i, '');
  name = name.replace(/\.(jpg|jpeg|png|gif)$/i, '');
  return name.replace(/\s+/g, ' ').trim();
}

function aggregateRawRows(values) {
  const map = {};
  values.forEach(function (r) {
    const campaign = String(r[COL.campaign] || '').trim();
    if (!campaign) return;
    const type = classifyType(r[COL.assetType]);
    if (!type) return;
    const cost = toNumber(r[COL.cost]);
    if (cost <= 0) return;
    const creative = cleanCreativeName(r[COL.creative], r[COL.asset]);
    if (!creative) return;
    const os = detectOs(campaign);
    const prereg = campaign.indexOf('사전') >= 0 ? 'Y' : 'N';
    const key = [os, type, prereg, creative].join('\u0001');
    const a = map[key] || (map[key] = { os: os, type: type, prereg: prereg, creative: creative, cost: 0, impressions: 0, installs: 0, convValue: 0, conversions: 0, rows: 0 });
    a.cost += cost;
    a.impressions += toNumber(r[COL.impressions]);
    a.installs += toNumber(r[COL.installs]);
    a.convValue += toNumber(r[COL.convValue]);
    a.conversions += toNumber(r[COL.conversions]);
    a.rows += 1;
  });
  return Object.keys(map)
    .map(function (k) { return map[k]; })
    .sort(function (x, y) { return y.cost - x.cost; })
    .map(function (a) {
      return [a.os, a.type, a.prereg, a.creative, Math.round(a.cost), Math.round(a.impressions),
        Math.round(a.installs * 100) / 100, Math.round(a.convValue), Math.round(a.conversions * 100) / 100, a.rows];
    });
}

function toCsv(rows) {
  return rows.map(function (row) {
    return row.map(function (v) {
      const s = String(v);
      return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    }).join(',');
  }).join('\r\n') + '\r\n';
}

// ---- Drive 입출력 ----

function getOrCreateFolder_(name) {
  const it = DriveApp.getRootFolder().getFoldersByName(name);
  return it.hasNext() ? it.next() : DriveApp.getRootFolder().createFolder(name);
}

function writeCsv_(folder, fileName, csv) {
  const it = folder.getFilesByName(fileName);
  if (it.hasNext()) {
    it.next().setContent(csv);
  } else {
    folder.createFile(fileName, csv, MimeType.CSV);
  }
}

if (typeof module !== 'undefined') {
  module.exports = { aggregateRawRows: aggregateRawRows, cleanCreativeName: cleanCreativeName, detectOs: detectOs, classifyType: classifyType, toNumber: toNumber, toCsv: toCsv };
}
