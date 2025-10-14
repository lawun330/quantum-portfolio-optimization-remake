import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def analyse_df(df, dim, ax1_ylim=[0,.01]):
    palette = "coolwarm"
    df['is_optimal'] = df['step3_rel_gap'].apply(lambda x: 1 if x==0 else 0)
    print('size:', len(df))
    # print(df[['experiment_id', 'is_optimal', dim]].groupby(dim).count())

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12,4))
    ax0.set_ylim([0,1])
    sns.barplot(df, x=dim, y='is_optimal', hue=dim, errorbar=None, ax=ax0, palette=palette)
    sns.boxplot(df, x=dim, y='last_improvement_iter', hue=dim, ax=ax1, palette=palette)


    # fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12,4))
    # ax2.sharey(ax1)
    # ax3.sharey(ax1)
    # ax2.get_yaxis().set_visible(False)
    # ax3.get_yaxis().set_visible(False)

    # sns.boxplot(df, x=dim, y='step3_rel_gap', hue=dim, ax=ax1)

    # sns.scatterplot(df, x='last_improvement_iter', y='step3_rel_gap', hue=dim, marker='o', legend=None,  ax=ax2)
    # # sns.scatterplot(df[df['step3_rel_gap']==0], x='last_improvement_iter', y='step3_rel_gap', marker='x', color='black', legend=None, ax=ax2)

    # sns.scatterplot(df, x='step3_x_hamming_weight', y='step3_rel_gap', hue=dim, legend=None,  ax=ax3)
    # # sns.scatterplot(df[df['step3_rel_gap']==0], x='step3_x_hamming_weight', y='step3_rel_gap', marker='x', color='black', legend=None, ax=ax3)
    # #plt.title('Simulator: TwoLocal(3 reps), 31 qubits, no local search')


    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12,4))
    ax1.set_ylim(ax1_ylim)
    ax2.sharey(ax1)
    ax3.sharey(ax1)
    ax2.get_yaxis().set_visible(False)
    ax3.get_yaxis().set_visible(False)

    sns.boxplot(df, x=dim, y='step3_rel_gap', hue=dim, ax=ax1, palette=palette)

    sns.scatterplot(df, x='last_improvement_iter', y='step3_rel_gap', hue=dim, marker='o', legend=None,  ax=ax2, palette=palette)
    # sns.scatterplot(df[df['step3_rel_gap']==0], x='last_improvement_iter', y='step3_rel_gap', marker='x', color='black', legend=None, ax=ax2)

    sns.scatterplot(df, x='step3_x_hamming_weight', y='step3_rel_gap', hue=dim, legend=None,  ax=ax3, palette=palette)
    # sns.scatterplot(df[df['step3_rel_gap']==0], x='step3_x_hamming_weight', y='step3_rel_gap', marker='x', color='black', legend=None, ax=ax3)
    #plt.title('Simulator: TwoLocal(3 reps), 31 qubits, no local search')




def analyse_df_step4(df, dim, ax1_ylim=[0,.01], num_iters=20):
    palette = "coolwarm"
    df['step3_is_optimal'] = df['step3_rel_gap'].apply(lambda x: 1 if x==0 else 0)
    df[f'step4_best_fx_{num_iters}iters'] = df['step4_iter_best_fx'].apply(lambda x: min(x[-num_iters:]))
    df[f'step4_rel_gap_{num_iters}iters'] = (df[f'step4_best_fx_{num_iters}iters'] - df['refvalue']) / df['refvalue']
    df[f'step4_is_optimal_{num_iters}iters'] = df[f'step4_rel_gap_{num_iters}iters'].apply(lambda x: 1 if x==0 else 0)

    print('size:', len(df))
    # print(df[['experiment_id', 'is_optimal', dim]].groupby(dim).count())

    fig, (ax0, ax0n, ax1, ax1n) = plt.subplots(1, 4, figsize=(12,4))
    ax0.set_ylim([0,1])
    ax0n.sharey(ax0)
    # ax0n.get_yaxis().set_visible(False)
    ax1.set_ylim(ax1_ylim)
    ax1n.sharey(ax1)
    # ax1n.get_yaxis().set_visible(False)
    sns.barplot(df, x=dim, hue=dim, y='step3_is_optimal', errorbar=None, ax=ax0, palette=palette)
    sns.barplot(df, x=dim, hue=dim, y=f'step4_is_optimal_{num_iters}iters', errorbar=None, ax=ax0n, palette=palette)
    sns.boxplot(df, x=dim, y='step3_rel_gap', hue=dim, ax=ax1, palette=palette)
    sns.boxplot(df, x=dim, y=f'step4_rel_gap_{num_iters}iters', hue=dim, ax=ax1n, palette=palette)

def analyse_df_step4_slide(df, dim, ax1_ylim=[0,.006], num_iters=20):
    palette = "coolwarm"
    df['step3_is_optimal'] = df['step3_rel_gap'].apply(lambda x: 1 if x==0 else 0)
    df[f'step4_best_fx_{num_iters}iters'] = df['step4_iter_best_fx'].apply(lambda x: min(x[-num_iters:]))
    df[f'step4_rel_gap_{num_iters}iters'] = (df[f'step4_best_fx_{num_iters}iters'] - df['refvalue']) / df['refvalue']
    df[f'step4_is_optimal_{num_iters}iters'] = df[f'step4_rel_gap_{num_iters}iters'].apply(lambda x: 1 if x==0 else 0)

    print('size:', len(df))
    # print(df[['experiment_id', 'is_optimal', dim]].groupby(dim).count())

    fig, (ax1, ax1n) = plt.subplots(1, 2, figsize=(6,4))
    ax1.set_ylim(ax1_ylim)
    ax1.set(xlabel='')
    ax1.tick_params(bottom=False)
    ax1.set_ylabel('relative gap')
    ax1.set_title('no local search')
    ax1n.sharey(ax1)
    ax1n.get_yaxis().set_visible(False)
    ax1n.set(xlabel='')
    ax1n.tick_params(bottom=False)
    ax1n.set_title('with local search')
    sns.boxplot(df, x=dim, y='step3_rel_gap', hue=dim, ax=ax1, palette=palette)
    sns.boxplot(df, x=dim, y=f'step4_rel_gap_{num_iters}iters', hue=dim, ax=ax1n, palette=palette)
