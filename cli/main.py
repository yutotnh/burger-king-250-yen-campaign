from playwright.sync_api import Playwright, sync_playwright

import argparse
import pprint


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="バーガーキングのキャンペーンからハンバーガーが1つ当たり250円のキャンペーンが開催中、もしくは開催予定であることを調べます"
    )

    # TODO 進行中のみや、将来のみ、進行中&将来の指定をするオプションを追加

    parser.parse_args()

    campaigns = []

    with sync_playwright() as playwright:
        campaigns = all_campaign_list(playwright)

    # タイトルに含まれていたら対象とする文字列
    target_campaigns = ["250円", "500円"]

    # 対象のキャンペーンのみを表示する
    for campaign in campaigns:
        if any(
            target_campaign in campaign["title"] for target_campaign in target_campaigns
        ):
            pprint.pprint(campaign)


def all_campaign_list(playwright: Playwright):
    """バーガーキングのキャンペーン一覧を取得する

    Parameters:
    ----------
    playwright: Playwright
        Playwrightのインスタンス

    Returns:
    ----------
    list[dict[str, str]]
        キャンペーンの一覧

    Examples:
    ----------
    >>> all_campaign_list(playwright)
    [
        {
            "start_date": "2023/12/15",
            "url": "https://www.burgerking.co.jp/#/campaignDetail/1548",
            "title": "年末年始の大特価！『チキンナゲット16ピース』が、 今だけ30%オフ210円引きの特別価格700円→490円！ みな様でも、おひとり様でも、お得にお楽しみください！"
        },
        {
            "start_date": "2023/12/01",
            "url": "https://www.burgerking.co.jp/#/campaignDetail/1539",
            "title": "2023年期間限定商品売上No.1 『マッシュルームワッパー 』に〈冬辛(ふゆから)〉バージョン新登場！ 新開発プレミアムチリチーズソースのマイルドな辛さが 直火焼きビーフときのこ4種に相性抜群"
        }
    ]

    Notes:
    ----------
    新規ページが開かれるタイプのキャンペーンは取得できない
    今回のツールで対象としているのは、新規ページが開かれないタイプのキャンペーンのため、今回は問題ない
    """

    browser = playwright.chromium.launch(headless=True)

    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.burgerking.co.jp/#/campaign/all")

    # ul.campBox内にキャンペーン一覧があるので一覧を取得する
    elements = page.query_selector_all("//ul[@class='campBox']/li")

    campains: list[dict[str, str]] = []

    # 1つ1つキャンペーンのタイトルと対象期間を取得する
    for i in range(len(elements)):
        campain: dict[str, str] = {}

        campaign_page = page.query_selector(f"//ul[@class='campBox']/li[{i + 1}]")

        if campaign_page is None:
            break

        start_date = page.query_selector(f"//ul[@class='campBox']/li[{i + 1}]/p/span")

        if start_date is None:
            break

        campain["start_date"] = start_date.inner_text()

        campaign_page.click()

        # 新規タブでHTMLが開かれた場合には対象のキャンペーンではない(はずな)ので、ページを閉じる
        # なぜかHTMLが開かれるクリックの直後ではなくその後のループで閉じられるので、ここで閉じる処理を入れている
        if 1 < len(context.pages):
            context.pages[1].close()

        # 新規タブでHTMLが開かれた場合には対象のキャンペーンではない(はずな)ので、スキップする
        if page.url.endswith("all"):
            continue

        page.wait_for_selector("//div[@class='camp_tit WEB']/h4")

        # 同じクラス
        title = page.query_selector("//div[@class='camp_tit WEB']/h4")
        if title is None:
            break

        campain["url"] = page.url
        campain["title"] = title.inner_text()

        campains.append(campain)

        page.go_back(wait_until="domcontentloaded")
        page.wait_for_selector("//ul[@class='campBox']/li")

    context.close()
    browser.close()

    return campains


if __name__ == "__main__":
    main()
