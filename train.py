import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
#from sklearn.feature_extraction.text import TfidfVectorizer
#from sklearn.cross_validation import train_test_split
from sklearn.grid_search import GridSearchCV
#from sklearn.cross_validation import cross_val_score
#from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
#from sklearn.pipeline import Pipeline
from scipy import sparse
#from sklearn.ensemble import RandomForestClassifier
from IPython.core.debugger import Tracer

tracer = Tracer()


def load_data():
    print("loading")
    comments = []
    dates = []
    labels = []

    with open("train.csv") as f:
        f.readline()
        for line in f:
            splitstring = line.split(',')
            labels.append(splitstring[0])
            dates.append(splitstring[1][:-1])
            comment = ",".join(splitstring[2:])
            comment = comment.strip().strip('"')
            comment.replace('_', ' ')
            comments.append(comment)
    labels = np.array(labels, dtype=np.int)
    dates = np.array(dates)
    return comments, dates, labels


def load_test():
    print("loading test set")
    comments = []
    dates = []

    with open("test.csv") as f:
        f.readline()
        for line in f:
            splitstring = line.split(',')
            dates.append(splitstring[0][:-1])
            comment = ",".join(splitstring[1:])
            comment = comment.strip().strip('"')
            comment.replace('_', ' ')
            comments.append(comment)
    dates = np.array(dates)
    return comments, dates


def write_test(labels, fname=None):
    if fname is None:
        fname = "test_prediction_%d.csv" % time()
    with open("test.csv") as f:
        with open(fname, 'w') as fw:
            fw.write(f.readline())
            for label, line in zip(labels, f):
                fw.write("%f," % label)
                fw.write(line)

#def get_fp_fn(clf, X, y, comments):
    #n_samples = X.shape[0]
    #inds = np.random.permutation(n_samples)


def get_features(comments, vectorizers=None):
    # get the google bad word list
    with open("google_badlist.txt") as f:
        badwords = [l.strip() for l in f.readlines()]
        badword_doc = " ".join(badwords)
    comments.append(badword_doc)

    print("vecorizing")
    if vectorizers is None:
        countvect = CountVectorizer(max_n=2)
        countvect_char = CountVectorizer(max_n=6, analyzer="char")
        #countvect = TfidfVectorizer()

        counts = countvect.fit_transform(comments)
        counts_char = countvect_char.fit_transform(comments)
    else:
        counts, counts_char = \
                [cv.transform(comments) for cv in vectorizers]

    counts = counts.tocsr()
    counts_char = counts_char.tocsr()

    badword_counts = counts[-1, :]
    counts = counts[:-1, :]
    counts_char = counts_char[:-1, :]
    comments.pop(-1)

    ## some handcrafted features!
    n_words = [len(c.split()) for c in comments]
    n_chars = [len(c) for c in comments]
    # number of uppercase words
    allcaps = [np.sum([w.isupper() for w in comment.split()])
           for comment in comments]
    # longest word
    max_word_len = [np.max([len(w) for w in c.split()]) for c in comments]
    # average word length
    mean_word_len = [np.mean([len(w) for w in c.split()]) for c in comments]
    # number of google badwords:
    n_bad = counts * badword_counts.T

    features = np.array([n_words, n_chars, allcaps, max_word_len,
        mean_word_len, n_bad.toarray()]).T

    features = sparse.hstack([counts, counts_char, features])
    if vectorizers is None:
        return features, (countvect, countvect_char)
    return features


def grid_search():
    comments, dates, labels = load_data()
    features, vectorizers = get_features(comments)

    tracer()
    #countvect = TfidfVectorizer()

    #param_grid = dict(logr__C=2. ** np.arange(-6, 4),
            #logr__penalty=['l1', 'l2'],
            #vect__max_n=np.arange(1, 4), vect__lowercase=[True, False])
    #param_grid = dict(C=2. ** np.arange(-3, 4),
            #penalty=['l1', 'l2'])
    param_grid = dict(C=2. ** np.arange(-5, 0),
            penalty=['l2'])
    #clf = LinearSVC(tol=1e-8, penalty='l1', dual=False, C=0.5)
    clf = LogisticRegression(tol=1e-8, penalty='l1', C=2)
    #pipeline = Pipeline([('vect', countvect), ('logr', clf)])
    #feature_selector.fit(comments, labels)
    #features = feature_selector.transform(comments).toarray()
    #clf = LinearSVC(tol=1e-8, penalty='l1', dual=False, C=0.5)
    clf = LogisticRegression(tol=1e-8)

    grid = GridSearchCV(clf, cv=5, param_grid=param_grid, verbose=4,
            n_jobs=11)
    #print(cross_val_score(clf, counts, labels, cv=3))

    grid.fit(features, labels)
    print(grid.best_score_)
    print(grid.best_params_)
    #clf.fit(X_train, y_train)
    #print(clf.score(X_test, y_test))
    tracer()
    comments_test, dates_test = load_test()
    features_test = get_features(comments_test, vectorizers)
    prob_pred = grid.best_estimator_.predict_proba(features_test)
    write_test(prob_pred[:, 1])

if __name__ == "__main__":
    grid_search()
