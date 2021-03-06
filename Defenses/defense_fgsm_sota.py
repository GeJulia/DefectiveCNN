import torch
import os
import IPython
import torch.nn as nn
import torch.nn.parallel
import os
import torchvision.transforms as transforms
from torch.autograd import Variable
import torchvision.datasets as datasets
import numpy as np
import csv
import matplotlib.image as mpimg

normalize = transforms.Normalize(mean=[0.4914, 0.4822, 0.4465], std=[0.2023, 0.1994, 0.2010])
val_loader = torch.utils.data.DataLoader(
        datasets.CIFAR10(root='./data', train=False, transform=transforms.Compose([
            transforms.ToTensor(),
            normalize,
        ])),
        batch_size=128, shuffle=False,
        num_workers=2, pin_memory=True)


total_num = 10000
net_names=['res32k4_full_5']
parameters = [8]
from resnet import ResNet18 as n00

class Ensemble(nn.Module):
    def __init__(self, net1, net2, net3, net4, net5):
        super(Ensemble, self).__init__()
        self.net1 = net1
        self.net2 = net2
        self.net3 = net3
        self.net4 = net4
        self.net5 = net5
    def forward(self, inputs):
        return (self.net1(inputs) + self.net2(inputs) + self.net3(inputs) + self.net4(inputs) + self.net5(inputs))/5
class Ensemble2(nn.Module):
    def __init__(self, net1, net2):
        super(Ensemble2, self).__init__()
        self.net1 = net1
        self.net2 = net2
    def forward(self, inputs):
        return (self.net1(inputs) + self.net2(inputs))/2
net00 = torch.nn.DataParallel(n00().cuda()).eval()
net00.load_state_dict(torch.load('./pytorch_cifar/checkpoint/ckpt3.t7')['net'])
net_dict = {
'norm'       : net00,
}
testdata_path_list = sorted(os.listdir('t_sample_testdata'),key=lambda x:int(x[:-6]))
for evaluate_name in net_dict.keys():
    print(evaluate_name)
    net = net_dict[evaluate_name]
    acc = []
    acc.append(evaluate_name)
    meanscore = []
    meanscore.append(evaluate_name)
    aeacc = []
    aeacc.append(evaluate_name)
    numcount = []
    numcount.append(evaluate_name)
    total = 0
    correct = 0
    for k in net_names:
        for parameter in parameters:
            stepsize = parameter
            imgdir = 'FGSM/'+k+'_'+str(stepsize)+'/'
            path_list = sorted(os.listdir(imgdir), key=lambda x:int(x[:-8]))
            labels = np.zeros(total_num)
            aelabels = np.zeros(total_num)
            successfool = np.zeros(total_num)
            scores = np.zeros(total_num)
            predicts = np.zeros(total_num)
            with torch.no_grad():
                for i,name in enumerate(path_list):
                    oriimg = mpimg.imread(imgdir + name)
                    labels[i] = int(name.split('.')[0].split('_')[1])
                    aelabels[i] = int(name.split('.')[0].split('_')[-1])
                    img = transforms.ToTensor()(oriimg).type(torch.FloatTensor)
                    img = normalize(img)
                    img = img.unsqueeze(0)
                    inputs = Variable(img.cuda())
                    outputs = net(inputs)
                    score, predicted = torch.max(nn.Softmax()(outputs), 1)
                    scores[i] = score.data.cpu().numpy()
                    predicts[i] = predicted.data.cpu().numpy()
            acc.append(np.mean(predicts==labels))
            aeacc.append(np.mean(predicts==aelabels))
            meanscore.append(np.mean(scores))
            numcount.append(total_num)
    with torch.no_grad():
        for data in val_loader:
            inputs, labels = data
            inputs = Variable(inputs.cuda())
            labels = Variable(labels.cuda())
            outputs = net(inputs)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    acc.append(100.*correct/total)
    w0 = csv.writer(open('fgsm_acc.csv','a'))
    w0.writerow(acc)
    w1 = csv.writer(open('fgsm_aeacc.csv','a'))
    w1.writerow(aeacc)
    w2 = csv.writer(open('fgsm_score.csv','a'))
    w2.writerow(meanscore)
    w3 = csv.writer(open('fgsm_num.csv','a'))
    w3.writerow(numcount)
