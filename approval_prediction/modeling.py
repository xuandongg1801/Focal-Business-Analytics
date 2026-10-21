"""Train-only preprocessing; bounded chronological validation; frozen test scoring."""
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, average_precision_score, confusion_matrix)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .config import FEATURES, SEED, TARGET_VERSION, validate_feature_names
from .registry import MODEL_REGISTRY, PREPROCESSOR_ARTIFACT


def metrics(y, probability, threshold):
    pred = np.asarray(probability) >= threshold
    both = len(np.unique(y)) == 2
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return dict(accuracy=accuracy_score(y, pred), precision=precision_score(y, pred, zero_division=0),
                recall=recall_score(y, pred, zero_division=0), f1=f1_score(y, pred, zero_division=0),
                macro_f1=f1_score(y, pred, average='macro', zero_division=0),
                roc_auc=roc_auc_score(y, probability) if both else np.nan,
                pr_auc=average_precision_score(y, probability) if both else np.nan,
                class_0_pr_auc=average_precision_score(1-np.asarray(y), 1-np.asarray(probability)) if both else np.nan,
                specificity=tn/(tn+fp) if tn+fp else np.nan,
                tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp))


def choose_threshold(y, probability):
    rows = [dict(threshold=float(t), **metrics(y, probability, t)) for t in np.linspace(.05, .95, 91)]
    table = pd.DataFrame(rows)
    # Macro F1 protects the smaller LOST group; positive F1 alone can favor always-positive.
    best = table.assign(distance=(table.threshold-.5).abs()).sort_values(
        ['macro_f1', 'f1', 'distance'], ascending=[False, False, True]).iloc[0]
    return float(best.threshold), table


def train_mlp(x, y, xv, yv, output):
    os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
    os.environ.setdefault('TF_DETERMINISTIC_OPS', '1')
    import tensorflow as tf
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.keras.utils.set_random_seed(SEED)
    tf.config.experimental.enable_op_determinism()
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(x.shape[1],)),
        tf.keras.layers.Dense(64, activation='relu'), tf.keras.layers.Dropout(.2),
        tf.keras.layers.Dense(32, activation='relu'), tf.keras.layers.Dropout(.2),
        tf.keras.layers.Dense(1, activation='sigmoid'),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(.001), loss='binary_crossentropy')
    # Explicit chronological validation, no implicit random validation_split.
    weights = {c: len(y)/(2*int((y == c).sum())) for c in (0, 1)}
    weights = weights if min(np.bincount(y))/len(y) < .4 else {0: 1., 1: 1.}
    callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=20,
                                                min_delta=1e-5, restore_best_weights=True)
    sample_weights = np.array([weights[int(label)] for label in y], dtype='float32')
    options = tf.data.Options()
    options.threading.private_threadpool_size = 1
    train_data = tf.data.Dataset.from_tensor_slices((x.astype('float32'), y, sample_weights))
    train_data = train_data.shuffle(len(y), seed=SEED, reshuffle_each_iteration=True).batch(32).with_options(options)
    valid_data = tf.data.Dataset.from_tensor_slices((xv.astype('float32'), yv)).batch(32).with_options(options)
    history = model.fit(train_data, validation_data=valid_data, epochs=250,
                        callbacks=[callback], shuffle=False, verbose=0)
    pd.DataFrame(history.history).assign(epoch=lambda d: np.arange(1, len(d)+1)).to_csv(
        output/'tables/mlp_learning_history.csv', index=False)
    model.save(output/MODEL_REGISTRY['mlp']['artifact'])
    return model, dict(epochs_run=len(history.history['loss']),
                       best_epoch=int(np.argmin(history.history['val_loss'])+1),
                       class_weights=weights, architecture='64-ReLU/Dropout(.2)/32-ReLU/Dropout(.2)/1-Sigmoid')


def probability(model, x, name):
    if name == 'mlp':
        return np.asarray(model(x.astype('float32'), training=False)).reshape(-1)
    return model.predict_proba(x)[:, 1]


def train_and_evaluate(dataset, out):
    from xgboost import XGBClassifier
    validate_feature_names(FEATURES)
    np.random.seed(SEED)
    splits = {name: dataset[dataset.split.eq(name)].copy() for name in ['train', 'validation', 'test']}
    for name, frame in splits.items():
        if frame.chot_don.nunique() != 2 or frame.chot_don.value_counts().min() < 10:
            raise ValueError(f'{name}: too few observations of a class for reliable evaluation')
    train, valid, test = [splits[n] for n in ['train', 'validation', 'test']]
    y, yv, yt = [s.chot_don.to_numpy(dtype=int) for s in [train, valid, test]]
    prep = Pipeline([('impute', SimpleImputer(strategy='median', keep_empty_features=True)),
                     ('scale', StandardScaler())])
    x = prep.fit_transform(train[FEATURES])
    xv = prep.transform(valid[FEATURES])
    joblib.dump(prep, out/PREPROCESSOR_ARTIFACT)
    pd.DataFrame({'order_id': train.order_id}).to_csv(out/'tables/preprocessor_fit_orders.csv', index=False)
    balanced = min(np.bincount(y))/len(y) < .4
    cw = 'balanced' if balanced else None
    candidates = {
        'logistic': [LogisticRegression(C=c, class_weight=cw, max_iter=2000, random_state=SEED) for c in [.1, 1., 10.]],
        'random_forest': [RandomForestClassifier(n_estimators=200, max_depth=depth,
                            min_samples_leaf=leaf, class_weight=cw, random_state=SEED, n_jobs=1)
                          for depth, leaf in [(4, 5), (6, 5), (6, 10)]],
        'xgboost': [XGBClassifier(n_estimators=400, max_depth=depth, learning_rate=.03,
                       min_child_weight=5, subsample=.8, colsample_bytree=.8, reg_lambda=5,
                       scale_pos_weight=float((y == 0).sum()/(y == 1).sum()) if balanced else 1,
                       objective='binary:logistic', eval_metric='logloss', early_stopping_rounds=25,
                       random_state=SEED, n_jobs=1, tree_method='hist') for depth in [2, 3]],
    }
    models, selections, search, thresholds, validation_probs = {}, {}, [], [], {}
    for name, estimators in candidates.items():
        ranked = []
        for index, estimator in enumerate(estimators):
            kwargs = {'eval_set': [(xv, yv)], 'verbose': False} if name == 'xgboost' else {}
            estimator.fit(x, y, **kwargs)
            p = probability(estimator, xv, name)
            threshold, curve = choose_threshold(yv, p)
            score = metrics(yv, p, threshold)
            search.append(dict(model=name, candidate=index, **score, threshold=threshold,
                               parameters=json.dumps(estimator.get_params(), default=str, sort_keys=True)))
            ranked.append((score['macro_f1'], score['roc_auc'], -index, estimator, threshold, curve, p))
        selected = max(ranked, key=lambda r: r[:3])
        _, _, _, model, threshold, curve, p = selected
        models[name] = model
        validation_probs[name] = p
        selections[name] = dict(threshold=threshold, **metrics(yv, p, threshold))
        thresholds.append(curve.assign(model=name))
        joblib.dump(model, out/MODEL_REGISTRY[name]['artifact'])
        print(f'{name}: validation macro F1={selections[name]["macro_f1"]:.4f}', flush=True)
    mlp, dl_info = train_mlp(x, y, xv, yv, out)
    models['mlp'] = mlp
    p = probability(mlp, xv, 'mlp')
    validation_probs['mlp'] = p
    threshold, curve = choose_threshold(yv, p)
    selections['mlp'] = dict(threshold=threshold, **metrics(yv, p, threshold))
    thresholds.append(curve.assign(model='mlp'))
    assert set(models) == set(MODEL_REGISTRY)
    winner = max(selections, key=lambda n: (selections[n]['macro_f1'], selections[n]['roc_auc']))
    # Persist choices BEFORE computing any test probabilities.
    frozen = dict(selected_model=winner, selection_metric='validation macro_f1; roc_auc tie-break', target_version=TARGET_VERSION,
                  selection=selections, mlp=dl_info, features=FEATURES,
                  trained_parameters={n: m.get_params() for n, m in models.items() if n != 'mlp'},
                  xgboost_best_iteration=int(models['xgboost'].best_iteration),
                  preprocessing_fit_split='train', preprocessing_fit_rows=len(train))
    (out/'models/selection.json').write_text(json.dumps(frozen, indent=2), encoding='utf-8')
    pd.DataFrame(search).to_csv(out/'tables/hyperparameter_search.csv', index=False)
    pd.concat(thresholds).to_csv(out/'tables/threshold_analysis.csv', index=False)
    pd.DataFrame.from_dict(selections, orient='index').rename_axis('model').reset_index().to_csv(
        out/'tables/validation_comparison.csv', index=False)
    vp = valid[['order_id', 'chot_don']].copy()
    for name, p in validation_probs.items():
        vp[f'prob_{name}'] = p
    vp.to_csv(out/'tables/validation_predictions.csv', index=False)
    xt = prep.transform(test[FEATURES])
    predictions = test[['order_id', 'order_date', 'customer_id', 'chot_don']].rename(columns={'chot_don': 'actual_chot_don'})
    comparisons, default_scores = [], []
    for name, model in models.items():
        prob = probability(model, xt, name)
        t = selections[name]['threshold']
        predictions[f'prob_{name}'] = prob
        predictions[f'pred_{name}'] = (prob >= t).astype(int)
        comparisons.append(dict(model=name, **metrics(yt, prob, t), threshold=t,
            **{f'validation_{k}': v for k, v in selections[name].items() if k != 'threshold'},
            **{f'test_{k}': v for k, v in metrics(yt, prob, t).items()},
            train_size=len(train), validation_size=len(valid), test_size=len(test),
            selected_on_validation=name == winner))
        default_scores.append(dict(model=name, **metrics(yt, prob, .5), threshold=.5))
    comparison = pd.DataFrame(comparisons)
    comparison.to_csv(out/'tables/model_comparison.csv', index=False)
    pd.DataFrame(default_scores).to_csv(out/'tables/default_threshold_comparison.csv', index=False)
    predictions.to_csv(out/'tables/transaction_approval_predictions.csv', index=False)
    # Retain all split predictions for transparent temporal diagnostics after selection.
    all_predictions = []
    for split, frame in splits.items():
        part = frame[['order_id', 'order_month', 'split', 'chot_don']].copy()
        for name, model in models.items():
            if split == 'train':
                probs = probability(model, x, name)
            elif split == 'validation':
                probs = validation_probs[name]
            else:
                probs = predictions[f'prob_{name}'].to_numpy()
            part[f'prob_{name}'] = probs
        all_predictions.append(part)
    pd.concat(all_predictions).to_csv(out/'tables/temporal_predictions.csv', index=False)
    # Interpretation on validation, never use test importance to reselect/tune.
    rng = np.random.default_rng(SEED)
    model = models[winner]
    base_auc = roc_auc_score(yv, probability(model, xv, winner))
    importance = []
    for j, feature in enumerate(FEATURES):
        deltas = []
        for _ in range(20):
            permuted = xv.copy()
            permuted[:, j] = rng.permutation(permuted[:, j])
            deltas.append(base_auc-roc_auc_score(yv, probability(model, permuted, winner)))
        importance.append(dict(feature=feature, importance=np.mean(deltas), std=np.std(deltas),
                               method='validation permutation ROC-AUC decrease', model=winner))
    imp = pd.DataFrame(importance).sort_values('importance', ascending=False)
    imp.to_csv(out/'tables/feature_importance.csv', index=False)
    pd.DataFrame({'feature': FEATURES, 'standardized_coefficient': models['logistic'].coef_[0]}).to_csv(
        out/'tables/logistic_coefficients.csv', index=False)
    for name in ['random_forest', 'xgboost']:
        pd.DataFrame({'feature': FEATURES, 'importance': models[name].feature_importances_}).to_csv(
            out/f'tables/{name}_feature_importance.csv', index=False)
    return comparison, predictions, imp, frozen
