import argparse

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Lasso
from sklearn.svm import SVR
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import DotProduct, WhiteKernel, RBF, Matern, RationalQuadratic
from sklearn.multioutput import RegressorChain
from lib.eval_metrics import EvalMetrics
from lib.dataset import DataUtils
global Data


class RegModels:

    def __init__(self, params):
        self.params = params
        self.train_x, self.train_y = Data.train_x, Data.train_y
        self.val_x, self.val_y = Data.val_x, Data.val_y
        self.test_x, self.test_y = Data.test_x, Data.test_y
        self.train_output = None
        self.model = None
        self.saved_model = None

    def train(self):
        pass

    def validate(self):
        self.train()
        self.saved_model = self.model

    def evaluate(self):

        test_labels = self.test_y.reshpae(self.test_y.shape[0] * self.test_y.shape[1], )
        outputs = self.saved_model.predict(self.test_x)
        outputs = np.array(outputs)
        predictions = outputs.reshape(outputs.shape[0] * outputs.shape[1], )
        eval_metric = EvalMetrics(test_labels, predictions)
        rmse = eval_metric.val_rmse()
        rse = eval_metric.val_rse()
        corr = eval_metric.val_corr()

        return rmse, rse, corr


class LRModel(RegModels):

    def __init__(self, params):
        super(LRModel, self).__init__(params)

    def train(self):
        self.model = LinearRegression()
        self.model.fit(self.train_x, self.train_y)
        self.train_output = self.model.predict(self.train_x)


class SVRModel(RegModels):

    def __init__(self, params):

        super(SVRModel, self).__init__(params)

    def train(self):
        self.model = SVR()
        self.model = RegressorChain(self.model)
        self.model.fit(self.train_x, self.train_y)
        self.train_output = self.model.predict(self.train_x)


class LassoModel(RegModels):

    def __init__(self, params):

        super(LassoModel, self).__init__(params)

    def train(self):
        self.model = Lasso()
        self.model = RegressorChain(self.model)
        self.model.fit(self.train_x, self.train_y)
        self.train_output = self.model.predict(self.train_x)


class GPModel(RegModels):

    def __init__(self, params):

        super(GPModel, self).__init__(params)
        self.kernel_ls = params.kernel_ls
        self.kernel = None

    def train(self):
        self.model = GaussianProcessRegressor(kernel=self.kernel)
        self.model.fit(self.train_x, self.train_y)
        self.train_output = self.model.predict(self.train_x)

    def validate(self):

        labels = self.val_y.reshape(self.val_y.shape[0] * self.val_y.shape[1], )

        best_val = float("inf")
        for kernel in self.kernel_ls:

            self.kernel = kernel
            self.train()
            output = self.model.predict(self.val_x)
            output = np.array(output)
            predictions = output.reshape(output.shape[0] * output.shape[1], )
            eval_metric = EvalMetrics(labels, predictions)
            rmse = eval_metric.val_rmse()

            if rmse < best_val:
                best_val = rmse
                self.saved_model = self.model


def main():
    parser = argparse.ArgumentParser(description='Keras Time series multi-output forecasting')
    parser.add_argument('--data_dir', default='../data', type=str)
    parser.add_argument('--window', type=int, default=16)
    parser.add_argument('--horizon', type=int, default=4)
    params = parser.parse_args()
    global Data
    Data = DataUtils(params.data_dir, params.window, params.horizon)

    # test GP
    parser.add_argument('--kernel_ls', default=[WhiteKernel() + DotProduct(), RBF(), Matern(), RationalQuadratic()])
    params_GP = parser.parse_args()
    gp_model = GPModel(params_GP)
    gp_model.validate()
    rmse, rse, corr = gp_model.evaluate()

    print("test rmse {:5.4f} | test rae {:5.4f} | test corr {:5.4f}".format(rmse, rse, rse))


if __name__ == '__main__':
    main()