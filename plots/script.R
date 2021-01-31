library(dplyr)
library(ggplot2)

plotChart <- function(endDate) {
  ggplot(df, aes(x=date)) +
    geom_line(aes(y=normalised_deaths), 
              color = '#bd0808', 
              size=1.5,
              alpha=0.1) +
    geom_line(data = filter(df, date < endDate),
              aes(y=normalised_deaths),
              color = '#bd0808',
              size = 1.5) +
    geom_line(aes(y=normalised_cases), 
              color = 'blue', 
              size=1.5,
              alpha = 0.1) +
    geom_line(data = filter(df, date < endDate),
              aes(y=normalised_cases),
              color = 'blue',
              size = 1.5) +
    # ggtitle("UK Mortality Rate") +
    scale_x_date(date_labels = "%b") +
    theme(panel.background = element_rect(fill = "transparent",colour = NA),
          plot.background = element_rect(fill = "transparent",colour = NA),
          panel.grid.major = element_line(size = 0.2, colour = "grey90"),
          text = element_text(size=32, color='grey70'),
          axis.title.x=element_blank(),
          axis.title.y=element_blank(),
          axis.text.y=element_blank(),
          axis.ticks.y=element_blank(),
    )
}

# data <- read.csv("https://covid.ourworldindata.org/data/owid-covid-data.csv")

df <- data %>%
  filter(iso_code == "GBR") %>%
  mutate(date = as.Date(date, "%Y-%m-%d"),
         normalised_cases = scale(new_cases_smoothed_per_million),
         normalised_deaths = scale(new_deaths_smoothed_per_million)
  )

plotDates = c("2020-03-11", "2020-03-12", "2020-03-17", "2020-03-23", "2020-04-11", 
              "2020-04-12", "2020-04-14", "2020-04-26", "2020-05-07", "2020-06-13",
              "2020-07-18")
plotList = list()

for (i in 1:length(plotDates)) {
  p = plotChart(plotDates[i])
  plotList[[i]] = p
} 

for (i in 1:length(plotList)) {
  fileName = sprintf("../images/DailyCovidDeaths_%s.svg", plotDates[i])
  print(fileName)
  ggsave(fileName, plotList[[i]], width=10, height=8, bg="transparent")
}

