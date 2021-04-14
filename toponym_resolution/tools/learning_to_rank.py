import pathlib
import subprocess

def convert_feature_file_format(filepath, filter):
    p = pathlib.Path(filepath)
    
    if filter == "exact":
        outfile = p.stem+"_exact-ranklib.tsv"
    elif filter == "notexact":
        outfile = p.stem+"_notexact-ranklib.tsv"
    else:
        outfile = p.stem+"_all-ranklib.tsv"
    out_file = "toponym_resolution/supervised_ranking/feature_files/" + outfile
    out = open(out_file,"w")

    features = open(filepath).read().strip().split("\n")[1:]
    current_qid = 0
    current_sub_id = 0
    for line in features:
        feat_vect = []
        line = line.split("\t")
        filter_flag = line[-1]
        if filter == "exact" and filter_flag!="1":
            continue
        if filter == "notexact" and filter_flag!="0":
            continue

        label = line[-2]
        cand = line[4]
        feat_vect.append(str(label))
        sub_id = line [2]
        if sub_id != current_sub_id:
            current_sub_id = sub_id
            current_qid+=1
        feat_vect.append("qid:"+str(current_qid))
        feat_counter = 1
        for f in range(5,14):
            feat_vect.append(str(feat_counter)+":"+str(line[f]))
            feat_counter+=1
        feat_vect.append("# "+ str(cand)+ " "+ str(current_sub_id))
        out.write(" ".join(feat_vect))
        out.write("\n")
    out.close()
    return out_file

def run_ranklib(dev_feat_file,test_feat_file,filter):
    dev = convert_feature_file_format(dev_feat_file,filter=filter)
    test = convert_feature_file_format(test_feat_file,filter="all")

    out = subprocess.check_output(["java", "-jar","/home/fnanni/Projects/PlaceLinking/toponym_resolution/tools/RankLib-2.13.jar","-train",dev,"-test",test,"-ranker","4","-metric2t","P@1", "-metric2T", "P@1","-save","/home/fnanni/Projects/PlaceLinking/toponym_resolution/supervised_ranking/models/model.run"])
    train_performance = out.decode("utf-8").split("\n")[-6]
    test_performance = out.decode("utf-8").split("\n")[-4]
    print (train_performance,test_performance)
    subprocess.check_output(["java", "-jar","/home/fnanni/Projects/PlaceLinking/toponym_resolution/tools/RankLib-2.13.jar","-load","toponym_resolution/supervised_ranking/models/model.run","-rank",test,"-indri","toponym_resolution/supervised_ranking/models/rank.txt"])
    rank = open("toponym_resolution/supervised_ranking/models/rank.txt","r").read().strip().split("\n")
    q_ids = set([x.split(" ")[3] for x in rank])

    results = {}

    for q_id in q_ids:
        scores = [[x.split(" ")[2],x.split(" ")[5]] for x in rank if x.split(" ")[3]==q_id]
        scores.sort(key=lambda x: x[1],reverse=True)
        results[q_id] = scores[0][0]
    return results



filter="exact"
dev_feat_file = "toponym_resolution/features_dev_deezy_match.tsv"
test_feat_file = "toponym_resolution/features_test_deezy_match.tsv"
run_ranklib(dev_feat_file,test_feat_file,filter)