"""
Kaming Yip
CS677 A1 Data Science with Python
Apr. 11, 2020
Assignment 10.1: SVM
"""

from pandas_datareader import data as web
import os
import pandas as pd
import numpy as np
from tabulate import tabulate
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix
from sklearn import svm

def main():
    def get_stock(ticker, start_date, end_date):
        """
        download the historical data from yahoo web
        & manipulate the data to create desirable columns
        """
        try:
            df = web.get_data_yahoo(ticker, start=start_date, end=end_date)
            df['Return'] = df['Adj Close'].pct_change()
            df['Return'].fillna(0, inplace = True)
            df['Return'] = 100.0 * df['Return']
            df['Return'] = df['Return'].round(3)
            df['Date'] = df.index
            df['Date'] = pd.to_datetime(df['Date'])
            df['Month'] = df['Date'].dt.month
            df['Year'] = df['Date'].dt.year
            df['Day'] = df['Date'].dt.day
            for col in ['Open', 'High', 'Low', 'Close', 'Adj Close']:
                df[col] = df[col].round(2)
            df['Weekday'] = df['Date'].dt.weekday_name  
            df['Week_Number'] = df['Date'].dt.strftime('%U')
            df['Year_Week'] = df['Date'].dt.strftime('%Y-%U')
            col_list = ['Date', 'Year', 'Month', 'Day', 'Weekday', 
                        'Week_Number', 'Year_Week', 'Open', 
                        'High', 'Low', 'Close', 'Volume', 'Adj Close',
                        'Return']
            num_lines = len(df)
            df = df[col_list]
            print('read', num_lines, 'lines of data for ticker:' , ticker)
            return df
        except Exception as error:
            print(error)
            return None
    
    # design the selected stock name and time frame
    try:
        ticker='YELP'
        input_dir = os.getcwd()
        output_file = os.path.join(input_dir, ticker + '.csv')
        df = get_stock(ticker, start_date='2016-01-01', end_date='2019-12-31')
        df.to_csv(output_file, index=False)
        print('wrote ' + str(len(df)) + ' lines to file: ' + ticker + '.csv', end = "\n\n" + "-" * 50 + "\n\n")
    except Exception as e:
        print(e)
        print('failed to get Yahoo stock data for ticker: ', ticker, end = "\n\n" + "-" * 50 + "\n\n")
       
    def weekly_return_volatility(data, start_date, end_date):
        """
        calculate the weekly mean return and volatility
        & create a new file to contain these infor
        """
        try:
            df_2 = data[data['Date'] >= start_date]
            df_2 = df_2[df_2['Date'] <= end_date]
            df_2 = df_2[['Year', 'Week_Number', 'Open', 'Adj Close', 'Return']]
            df_2.index = range(len(df_2))
            df_grouped = df_2.groupby(['Year', 'Week_Number'])['Return'].agg([np.mean, np.std])
            df_grouped.reset_index(['Year', 'Week_Number'], inplace=True)
            df_grouped.rename(columns={'mean': 'mean_return', 'std':'volatility'}, inplace=True)
            df_grouped.fillna(0, inplace=True)
            df_grouped["Open"] = df_2.groupby(["Year", "Week_Number"])["Open"].head(1).\
                                 reset_index(drop = True).copy()
            df_grouped["Adj Close"] = df_2.groupby(["Year", "Week_Number"])["Adj Close"].tail(1).\
                                      reset_index(drop = True).copy()
            return df_grouped
        except Exception as error:
            print(error)
            return None
    
    # create the weekly dataframe with mean return and volatility values
    try:
        df_weekly = weekly_return_volatility(df, start_date='2018-01-01', end_date='2019-12-31')
    except Exception as e:
        print("Error in weekly_return_volatility: ", end = " ")
        print(e)
    
    def weekly_label(data, year):
        """
        to create labels
        """
        try:
            df_label = data[data["Year"] == year].copy()
            mean_return_percent50 = np.percentile(df_label["mean_return"], 50)
            volatility_percent50 = np.percentile(df_label["volatility"], 50)      
            df_label["True Label"] = np.where((df_label["mean_return"] >= mean_return_percent50) & \
                                              (df_label["volatility"] <= volatility_percent50), "Green", "Red")
            return df_label
        except Exception as error:
            print(error)
            return None
        
    try:
        df_labeling = pd.DataFrame()
        for year in [2018, 2019]:
            df_year_label = weekly_label(df_weekly, year)
            label_count = df_year_label.groupby("True Label")["True Label"].size().to_frame(name = "Freq")
            print("Label Count for Year {0}".format(year))
            print(tabulate(label_count, headers = "keys", numalign = "right"), end = "\n\n")         
            df_labeling = df_labeling.append(df_year_label, ignore_index = True)
        df_labeling["Week_Number"] = df_labeling["Week_Number"].astype(int)
    except Exception as e:
        print("Error in weekly_label:", end = " ")
        print(e)
        
    def SVM(train_data, test_data, predictor, method, degree = 2):
        # train the SVM model by stock data in year 1
        train_X = train_data[predictor].values
        scaler = StandardScaler().fit(train_X)
        train_X = scaler.transform(train_X)
        train_Y = train_data["True Label"].values
        svm_classifier = svm.SVC(kernel = method, degree = degree)
        svm_classifier.fit(train_X, train_Y)
        
        # predict the labels in year 2
        test_X = test_data[predictor].values
        test_X = scaler.transform(test_X)
        pred_Y = svm_classifier.predict(test_X)
        return pred_Y
    
    def designed_confusion_matrix(actual, pred):
        cm = confusion_matrix(actual, pred)
        list_of_tuples = list(zip(cm[0], cm[1]))
        designed_cm = pd.DataFrame(list_of_tuples,
                                   columns = ["Actual Green", "Actual Red"],
                                   index = ["Predicted Green", "Predicted Red"])
        diagonal_sum = cm.trace()
        sum_of_all_elements = cm.sum()
        accuracy = diagonal_sum / sum_of_all_elements
        TPR = cm[0,0]/(cm[0,0] + cm[0,1])
        TNR = cm[1,1]/(cm[1,0] + cm[1,1])
        return designed_cm, accuracy, TPR, TNR
    
    def printout(actual, pred, classifier_type):
        cm, accuracy, TPR, TNR = designed_confusion_matrix(actual, pred)
        print(" * The Confusion Matrix for {0} * ".format(classifier_type),
              cm,
              "The accuracy of this model is {0:.3f}.\n".format(accuracy) +\
              "The true positive rate of this model is {0:.3f}.\n".format(TPR) +\
              "The true negative rate of this model is {0:.3f}.\n".format(TNR),
              sep = "\n\n", end = "\n\n")
        return accuracy
    
    def trade_with_labels(data, col_name):
        money = 100.0
        shares = 0.0
        position = "No"
        balance = []
        df_trade_labels = data.copy()
        for i in range(len(df_trade_labels) - 1):
            if i == 0:
                label = df_trade_labels.iloc[i][col_name]
                if label == "Green":
                    shares = money / df_trade_labels.iloc[i]["Open"]
                    money = 0.0
                    position = "Long"
                    balance.append(shares * df_trade_labels.iloc[i]["Adj Close"])
                else:
                    balance.append(money)              
            else:
                label = df_trade_labels.iloc[i+1][col_name]
                if label == "Red":
                    if position == "Long":
                        money = shares * df_trade_labels.iloc[i]["Adj Close"]
                        shares = 0.0
                        position = "No"
                    balance.append(money)
                else:
                    if position == "No":
                        shares = money / df_trade_labels.iloc[i+1]["Open"]
                        money = 0.0
                        position = "Long"
                    balance.append(shares * df_trade_labels.iloc[i]["Adj Close"])            
        if position == "Long":
            balance.append(shares * df_trade_labels.iloc[-1]["Adj Close"])
        else:
            balance.append(money)
        return balance
        
    def script_text(data, year, col_name):
        label_text_max = "{0} Week {1}\nmax ${2}".\
                         format(year,
                                data.iloc[data[data["Year"] == year][col_name].idxmax()]["Week_Number"],
                                round(data[data["Year"] == year][col_name].max(), 2))
        label_x_max = data[data["Year"] == year][col_name].idxmax()
        label_y_max = round(data[data["Year"] == year][col_name].max(), 2)
            
        label_text_min = "{0} Week {1}\nmin ${2}".\
                         format(year,
                                data.iloc[data[data["Year"] == year][col_name].idxmin()]["Week_Number"],
                                round(data[data["Year"] == year][col_name].min(), 2))
        label_x_min = data[data["Year"] == year][col_name].idxmin()
        label_y_min = round(data[data["Year"] == year][col_name].min(), 2)
            
        label_text_final = "{0} Final:\n${1}".format(year, round(data[data["Year"] == year].iloc[-1][col_name], 2))
        label_x_final = data[data["Year"] == year].tail(1).index.values
        label_y_final = round(data[data["Year"] == year].iloc[-1][col_name], 2)
       
        return label_text_max, label_x_max, label_y_max,\
                   label_text_min, label_x_min, label_y_min,\
                       label_text_final, label_x_final, label_y_final
    
    def buy_n_hold(data):
        money = 100.0
        shares = 0.0
        balance = []
        df_buy_hold = data.copy()  
        for i in range(len(df_buy_hold)):
            if i == 0:
                shares = money / df_buy_hold.iloc[i]["Open"]
            balance.append(shares * df_buy_hold.iloc[i]["Adj Close"])
        return balance

    ########## Q1 & Q2 & Q3 ##########
    print("\n" + "#" * 20 + " Q1 & Q2 & Q3 " + "#" * 20 + "\n")
    try:
        df_2018 = df_labeling.loc[df_labeling["Year"] == 2018].copy().reset_index(drop = True)
        df_2019 = df_labeling.loc[df_labeling["Year"] == 2019].copy().reset_index(drop = True)
        Y_2019 = df_2019[["True Label"]].values
        # Linear SVM
        linear_pred_Y = SVM(df_2018, df_2019, ["mean_return", "volatility"], "linear")
        linear_accuracy = printout(Y_2019, linear_pred_Y, "Linear SVM")
    except Exception as e:
        print("Error in Question 1&2&3:", end = " ")
        print(e)
    
    ########## Q4 ##########
    print("\n" + "#" * 25 + " Q4 " + "#" * 25 + "\n")
    try:
        # Gaussian SVM
        gaussian_pred_Y = SVM(df_2018, df_2019, ["mean_return", "volatility"], "rbf")
        gaussian_accuracy = printout(Y_2019, gaussian_pred_Y, "Gaussian SVM")
        print("The accuracy of Gaussian SVM ({0:.3f}) is {1}\nthe accuracy of Linear SVM ({2:.3f}).".\
              format(gaussian_accuracy,
                     "the same as" if gaussian_accuracy == linear_accuracy else\
                      ("better than" if gaussian_accuracy > linear_accuracy else\
                       "worse than"),
                     linear_accuracy))
    except Exception as e:
        print("Error in Question 4:", end = " ")
        print(e)
    
    ########## Q5 ##########
    print("\n" + "#" * 25 + " Q5 " + "#" * 25 + "\n")
    try:
        # Polynomial SVM for degree 2
        poly_pred_Y = SVM(df_2018, df_2019, ["mean_return", "volatility"], "poly", degree = 2)
        poly_accuracy = printout(Y_2019, poly_pred_Y, "Polynomial SVM")
        print("The accuracy of Polynomial SVM ({0:.3f}) is {1}\nthe accuracy of Linear SVM ({2:.3f}).".\
              format(poly_accuracy,
                     "the same as" if poly_accuracy == linear_accuracy else\
                      ("better than" if poly_accuracy > linear_accuracy else\
                       "worse than"),
                     linear_accuracy))
    except Exception as e:
        print("Error in Question 5:", end = " ")
        print(e)
    
    ########## Q6 ##########
    print("\n" + "#" * 35 + " Q6 " + "#" * 35 + "\n")
    try:
        df_trading = df_labeling[df_labeling["Year"] == 2019].copy().reset_index(drop = True)
        df_trading["True Label Balance"] = trade_with_labels(df_trading, "True Label")
        df_trading["Buy and Hold Balance"] = buy_n_hold(df_trading)
        df_trading["Linear SVM Label"] = linear_pred_Y
        df_trading["Linear SVM Balance"] = trade_with_labels(df_trading, "Linear SVM Label")
        
        fig, ax = plt.subplots(figsize = (9, 5))
        
        label_text_max_2019, label_x_max_2019, label_y_max_2019,\
            label_text_min_2019, label_x_min_2019, label_y_min_2019,\
                label_text_final_2019, label_x_final_2019, label_y_final_2019 =\
                    script_text(df_trading, 2019, "True Label Balance")
        
        linearSVM_text_max_2019, linearSVM_x_max_2019, linearSVM_y_max_2019,\
            linearSVM_text_min_2019, linearSVM_x_min_2019, linearSVM_y_min_2019,\
                linearSVM_text_final_2019, linearSVM_x_final_2019, linearSVM_y_final_2019 =\
                    script_text(df_trading, 2019, "Linear SVM Balance")
        
        buy_hold_text_max_2019, buy_hold_x_max_2019, buy_hold_y_max_2019,\
            buy_hold_text_min_2019, buy_hold_x_min_2019, buy_hold_y_min_2019,\
                buy_hold_text_final_2019, buy_hold_x_final_2019, buy_hold_y_final_2019 =\
                    script_text(df_trading, 2019, "Buy and Hold Balance")
        
        # Trading with True Label
        ax.plot(df_trading.index, "True Label Balance", data = df_trading, color = "blue")
        
        ax.annotate(label_text_max_2019, xy = (label_x_max_2019, label_y_max_2019), xycoords = "data",
                    xytext = (label_x_max_2019+5, label_y_max_2019+5), color = "blue",
                    arrowprops = dict(arrowstyle = "->", connectionstyle = "angle,angleA=0,angleB=90", color = "blue"),
                    ha = "left", va = "bottom")
        ax.annotate(label_text_min_2019, xy = (label_x_min_2019, label_y_min_2019), xycoords = "data",
                    xytext = (label_x_min_2019+2, label_y_min_2019+17), color = "blue",
                    arrowprops = dict(arrowstyle = "->", connectionstyle = "angle,angleA=0,angleB=90", color = "blue"),
                    ha = "left", va = "bottom")
        ax.annotate(label_text_final_2019, xy = (label_x_final_2019, label_y_final_2019), xycoords = "data",
                    xytext = (label_x_final_2019+5, label_y_final_2019-10), color = "blue",
                    arrowprops = dict(arrowstyle = "->", connectionstyle = "angle,angleA=0,angleB=90", color = "blue"),
                    ha = "left", va = "bottom")
        
        # Buy and Hold
        ax.plot(df_trading.index, "Buy and Hold Balance", data = df_trading, color = "red")
        
        ax.annotate(buy_hold_text_max_2019, xy = (buy_hold_x_max_2019, buy_hold_y_max_2019), xycoords = "data",
                    xytext = (buy_hold_x_max_2019+5, buy_hold_y_max_2019+11), color = "red",
                    arrowprops = dict(arrowstyle = "->", connectionstyle = "angle,angleA=0,angleB=90", color = "red"),
                    ha = "left", va = "bottom")
        ax.annotate(buy_hold_text_min_2019, xy = (buy_hold_x_min_2019, buy_hold_y_min_2019), xycoords = "data",
                    xytext = (buy_hold_x_min_2019+4, buy_hold_y_min_2019+2), color = "red",
                    arrowprops = dict(arrowstyle = "->", connectionstyle = "angle,angleA=0,angleB=90", color = "red"),
                    ha = "left", va = "bottom")
        ax.annotate(buy_hold_text_final_2019, xy = (buy_hold_x_final_2019, buy_hold_y_final_2019), xycoords = "data",
                    xytext = (buy_hold_x_final_2019+5, buy_hold_y_final_2019+5), color = "red",
                    arrowprops = dict(arrowstyle = "->", connectionstyle = "angle,angleA=0,angleB=90", color = "red"),
                    ha = "left", va = "bottom")
        
        # Trading with Linear SVM Label
        ax.plot(df_trading.index, "Linear SVM Balance", data = df_trading, color = "green")
        
        ax.annotate(linearSVM_text_max_2019, xy = (linearSVM_x_max_2019, linearSVM_y_max_2019), xycoords = "data",
                    xytext = (linearSVM_x_max_2019+5, linearSVM_y_max_2019+5), color = "green",
                    arrowprops = dict(arrowstyle = "->", connectionstyle = "angle,angleA=0,angleB=90", color = "green"),
                    ha = "left", va = "bottom")
        ax.annotate(linearSVM_text_min_2019, xy = (linearSVM_x_min_2019, linearSVM_y_min_2019), xycoords = "data",
                    xytext = (linearSVM_x_min_2019+5, linearSVM_y_min_2019+40), color = "green",
                    arrowprops = dict(arrowstyle = "->", connectionstyle = "angle,angleA=0,angleB=90", color = "green"),
                    ha = "left", va = "bottom")
        ax.annotate(linearSVM_text_final_2019, xy = (linearSVM_x_final_2019, linearSVM_y_final_2019), xycoords = "data",
                    xytext = (linearSVM_x_final_2019+5, linearSVM_y_final_2019-15), color = "green",
                    arrowprops = dict(arrowstyle = "->", connectionstyle = "angle,angleA=0,angleB=90", color = "green"),
                    ha = "left", va = "bottom")
        
        plt.title("* Year 2019 *\n" + "Performance against Different Investing Strategies", loc = "center")
        plt.xlabel("Week Number")
        plt.xticks(np.arange(0, 60, 5))
        plt.ylabel("Total Balance($)")
        plt.legend()
        plt.show()
        
        print("\nAs displayed in the plot above, the {0} strategy results in a".\
              format("buy-and-hold" if buy_hold_y_final_2019 > linearSVM_y_final_2019 else "Linear SVM"),
              "larger amount as ${0} at the end of the year 2019.".\
              format(buy_hold_y_final_2019 if buy_hold_y_final_2019 > linearSVM_y_final_2019 else linearSVM_y_final_2019),
              sep = "\n")
        
    except Exception as e:
        print("Error in Question 6:", end = " ")
        print(e)

main()    
