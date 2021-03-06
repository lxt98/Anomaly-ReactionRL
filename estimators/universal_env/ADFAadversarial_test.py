import json
import numpy as np
import pandas as pd
from keras.models import model_from_json
import matplotlib.pyplot as plt
from ADFAadversarialAD import huber_loss

import itertools
from sklearn.metrics import f1_score
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.metrics import  confusion_matrix

from network_classification import NetworkClassificationEnv




def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    print(cm)

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')









formated_test_path = "../../datasets/formated/formated_test_ADFA.data"

########################################################################
# Aguments needed by enviroment:

# Map from attack to type
attack_map = {'Normal': 'Normal',
              'Generic': 'Generic',
              'Exploits': 'Exploits',
              'Fuzzers':'Fuzzers',
              'DoS':'DoS',
              'Reconnaissance':'Reconnaissance',
              'Analysis':'Analysis',
              'Backdoor':'Backdoor',
              'Shellcode':'Shellcode',
              'Worms':'Worms'
            }



##########################################################################

env = NetworkClassificationEnv('test',
        attack_map,
        formated_test_path = formated_test_path
        )
    



with open("models/ADFA_agent_model.json", "r") as jfile:
    model = model_from_json(json.load(jfile))
model.load_weights("models/ADFA_agent_model.h5")

model.compile(loss=huber_loss,optimizer="sgd")


total_reward = 0    


true_labels = np.zeros(len(env.attack_types),dtype=int)
estimated_labels = np.zeros(len(env.attack_types),dtype=int)
estimated_correct_labels = np.zeros(len(env.attack_types),dtype=int)

#states , labels = env.get_sequential_batch(test_path,batch_size = env.batch_size)
states , labels = env.get_full()
q = model.predict(states)
actions = np.argmax(q,axis=1)        



labs,counts = np.unique(labels,return_counts=True)
true_labels[labs] += counts

labs,counts = np.unique(actions,return_counts=True)
estimated_labels[labs] += counts

correct = np.where(labels==actions)
total_reward = len(np.array(correct)[0])

estimated_correct = labels[correct]
labs,count = np.unique(estimated_correct,return_counts=True)
estimated_correct_labels[labs] = count

#action_dummies = pd.get_dummies(actions)
#
#posible_actions = np.arange(len(env.attack_types))
#for non_existing_action in posible_actions:
#    if non_existing_action not in action_dummies.columns:
#        action_dummies[non_existing_action] = np.uint8(0)
#labels_dummies = pd.get_dummies(labels)




acc = float(100*total_reward/len(states))
print('\r\nTotal reward: {} | Number of samples: {} | Accuracy = {:.2f}%'.format(total_reward,
      len(states),acc))
outputs_df = pd.DataFrame(index = env.attack_types,columns = ["Estimated","Correct","Total" ])
for indx,att in enumerate(env.attack_types):
   outputs_df.iloc[indx].Estimated = estimated_labels[indx]
   outputs_df.iloc[indx].Correct = estimated_correct_labels[indx]
   outputs_df.iloc[indx].Total = true_labels[indx]


##############





        

    #%%

print(outputs_df)

fig, ax = plt.subplots()
width = 0.35
pos = np.arange(len(true_labels))
p1 = plt.bar(pos, estimated_correct_labels,width,color='g')
p1 = plt.bar(pos+width,
             (np.abs(estimated_correct_labels-true_labels)),width,
             color='r')
p2 = plt.bar(pos+width,np.abs(estimated_labels-estimated_correct_labels),width,
             bottom=(np.abs(estimated_correct_labels-true_labels)),
             color='b')


ax.set_xticks(pos+width/2)
ax.set_xticklabels(env.attack_types,rotation='vertical')
#ax.set_yscale('log')

#ax.set_ylim([0, 100])
ax.set_title('Test set scores, Acc = {:.2f}'.format(acc))
plt.legend(('Correct estimated','False negative','False positive'))
plt.tight_layout()
#plt.show()
plt.savefig('results/test_adv_imp.svg', format='svg', dpi=1000)


#%% Agregated precision

aggregated_data_test = labels

print('Performance measures on Test data')
print('Accuracy =  {:.4f}'.format(accuracy_score( aggregated_data_test,actions)))
print('F1 =  {:.4f}'.format(f1_score(aggregated_data_test,actions, average='weighted')))
print('Precision_score =  {:.4f}'.format(precision_score(aggregated_data_test,actions, average='weighted')))
print('recall_score =  {:.4f}'.format(recall_score(aggregated_data_test,actions, average='weighted')))

cnf_matrix = confusion_matrix(aggregated_data_test,actions)
np.set_printoptions(precision=2)
plt.figure()
plt.figure()
plot_confusion_matrix(cnf_matrix, classes=env.attack_types, normalize=True,
                      title='Normalized confusion matrix')
plt.savefig('results/confusion_matrix_adversarial_ADFA.svg', format='svg', dpi=1000)

