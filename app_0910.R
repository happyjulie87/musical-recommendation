library(shiny)
library(readxl)
library(dplyr)
library(stringr)
library(rvest)
library(httr)

# 讀取音樂劇資料（請確認檔名與欄位正確）
musicals <- read_excel("muiscal titles_all.xlsx")

# 問卷題目（簡化版）
questions <- list(
  "開放性" = c("我喜歡奇幻想像的劇情", "我偏好新穎、實驗性強的作品"),
  "嚴謹性" = c("我會查閱表演背景", "我在意劇情邏輯"),
  "外向性" = c("我喜歡熱鬧華麗的歌舞", "我偏好與朋友一起觀賞"),
  "親和性" = c("我容易被情感感動", "我喜歡溫暖人性關懷的故事"),
  "神經質" = c("我偏好張力強、懸疑劇情", "劇情高潮時我會感到緊張")
)

# 擷取 KOPIS 圖片
get_kopis_image <- function(title) {
  search_url <- paste0("https://kopis.or.kr/search?query=", URLencode(title))
  tryCatch({
    page <- read_html(search_url)
    img_node <- html_node(page, "div.poster img")
    img_url <- html_attr(img_node, "src")
    if (!is.null(img_url)) {
      return(img_url)
    } else {
      return(NULL)
    }
  }, error = function(e) {
    return(NULL)
  })
}

# UI
ui <- fluidPage(
  titlePanel("🎭 人格測驗音樂劇推薦系統"),
  sidebarLayout(
    sidebarPanel(
      lapply(names(questions), function(trait) {
        tagList(
          h4(trait),
          lapply(questions[[trait]], function(q) {
            sliderInput(
              inputId = paste0(trait, "_", str_sub(q, 1, 5)),
              label = q,
              min = 1, max = 5, value = 3
            )
          })
        )
      }),
      actionButton("submit", "產生推薦")
    ),
    mainPanel(
      h3("🎬 推薦音樂劇"),
      uiOutput("recommend_ui")
    )
  )
)

# Server
server <- function(input, output) {
  observeEvent(input$submit, {
    traits <- names(questions)
    user_scores <- sapply(traits, function(trait) {
      mean(sapply(questions[[trait]], function(q) {
        input[[paste0(trait, "_", str_sub(q, 1, 5))]]
      }))
    })
    
    # 計算推薦分數差距
    musicals$score_diff <- apply(musicals[, traits], 1, function(row) {
      sum(abs(row - user_scores))
    })
    
    top_musicals <- musicals %>%
      arrange(score_diff) %>%
      head(5)
    
    # 顯示推薦卡片
    output$recommend_ui <- renderUI({
      lapply(1:nrow(top_musicals), function(i) {
        row <- top_musicals[i, ]
        img_url <- get_kopis_image(row$`作品名稱(中英譯名)`)
        
        tagList(
          h4(row$`作品名稱(中英譯名)`),
          if (!is.null(img_url)) {
            tags$img(src = img_url, width = "300px")
          },
          p(strong("類型："), row$類型),
          p(strong("介紹："), row$作品內容介紹),
          tags$a(
            href = paste0("https://kopis.or.kr/search?query=", URLencode(row$`作品名稱(中英譯名)`)),
            "🔗 查看更多資訊", target = "_blank"
          ),
          hr()
        )
      })
    })
  })
}

# 啟動 App
shinyApp(ui = ui, server = server)






