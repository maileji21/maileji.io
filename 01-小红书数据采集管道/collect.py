from DrissionPage import ChromiumPage, ChromiumOptions
import random, time
import storage

MAX_PAGES = 30
API = "https://so.xiaohongshu.com/api/sns/web/v2/search/notes"

def build_page(retries=3):
    """启动浏览器；用户目录锁没释放时等几秒重试"""
    co = ChromiumOptions().set_user_data_path("./browser_data")
    for i in range(retries):
        try:
            page = ChromiumPage(co)
            page.listen.start(API, method="POST")
            return page
        except Exception as e:
            print(f"  浏览器启动失败({i+1}/{retries}): {e.__class__.__name__}，等 5s 重试")
            time.sleep(5)
    raise RuntimeError("浏览器连续启动失败，检查是否有残留 Chrome 进程")


def wait_packet(page, timeout=8):
    pkt = page.listen.wait(count=1, timeout=timeout, raise_err=False)
    return pkt or None


def scroll_for_page(page, tries=4):
    """滚到底等响应，失败就补滚一次再等；彻底拿不到返回 None"""
    for _ in range(tries):
        page.scroll.to_bottom()
        time.sleep(random.uniform(1.2, 2.0))
        pkt = wait_packet(page, timeout=8)
        if pkt:
            return pkt
        page.scroll.down(1200)          # 兜底：小步补滚，重新触发懒加载
        time.sleep(0.8)
    return None


def parse_items(items):
    batch, skipped = [], 0
    for item in items:
        nc = item.get("note_card")
        if not nc:                      # 热搜词 / 推荐位
            skipped += 1
            continue
        ii = nc.get("interact_info") or {}
        user = nc.get("user") or {}
        batch.append({
            "note_id":   item["id"],
            "title":     nc.get("display_title"),
            "author":    user.get("nickname"),
            "author_id": user.get("user_id"),
            "liked":     storage.parse_count(ii.get("liked_count")),
            "collected": storage.parse_count(ii.get("collected_count")),
            "comment":   storage.parse_count(ii.get("comment_count")),
            "shared":    storage.parse_count(ii.get("shared_count")),
            "note_url":  f"https://www.xiaohongshu.com/explore/{item['id']}"
                         f"?xsec_token={item.get('xsec_token', '')}",
        })
    return batch, skipped


def log_page(conn, keyword, page_no, raw, ins, upd, skipped, cost):
    """把一页的采集结果写进 crawl_log"""
    conn.execute(
        "INSERT INTO crawl_log (platform,keyword,page_no,raw,new_cnt,dup_cnt,skipped,cost_s,ts)"
        " VALUES (?,?,?,?,?,?,?,?, datetime('now','localtime'))",
        ("xiaohongshu", keyword, page_no, raw, ins, upd, skipped, cost),
    )
    conn.commit()


def crawl(keyword, max_pages=30):
    """每个词独立开一次浏览器。上午验证过：这个结构监听稳定；共享浏览器会有监听失效风险"""
    conn = storage.get_conn()
    page = build_page()
    try:
        page.get(f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_explore_feed")
        time.sleep(5)

        pkt = wait_packet(page, timeout=12)
        page_no = zero_streak = 0
        t0 = time.time()
        pending = None          # 上一页的记录，等翻页结束拿到耗时再落库

        while pkt and page_no < max_pages:
            page_no += 1
            t_page = time.time()

            items = pkt.response.body["data"]["items"]
            batch, skipped = parse_items(items)
            ins, upd = storage.save_notes(conn, batch)
            print(f"第{page_no:>2}页 {len(items):>2}条 新{ins:>3} 重{upd:>3} 跳过{skipped}")

            if pending:         # 补记上一页，此时已包含它的翻页等待时间
                log_page(conn, keyword, *pending[:5], cost=round(t_page - pending[5], 2))
            pending = (page_no, len(items), ins, upd, skipped, t_page)

            if ins == 0:                      # 连续两页没新增 → 已采过，提前停
                zero_streak += 1
                if zero_streak >= 2:
                    print("  连续 2 页无新增，提前终止")
                    break
            else:
                zero_streak = 0

            page.listen.clear()
            pkt = scroll_for_page(page)

        if pending:             # 循环结束时补记最后一页
            log_page(conn, keyword, *pending[:5], cost=round(time.time() - pending[5], 2))

        used = time.time() - t0
        print(f"[{keyword}] {page_no} 页 / {used:.0f}s / 平均 {used / max(page_no, 1):.1f}s 每页")
        print(storage.stats(conn))
    finally:
        page.quit()


if __name__ == "__main__":
    for kw in ["小个子穿搭"]:      # 「女生穿搭」已采过；今天不再跑，换到明天
        crawl(kw)
        time.sleep(8)             # 词间停 8s，让用户目录锁释放，也给站点喘息
