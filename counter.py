def get_options(votes):
    options = set()
    for vote in votes:
        for pref in vote:
            options.add(pref)
    return options

def find_eliminated(counted_votes):
    min_count = sys.maxsize
    for count in counted_votes.values():
        if count < min_count:
            min_count = count
    eliminated = set()
    for count in counted_votes.items():
        if count[1] == min_count:
            eliminated.add(count[0])
    return eliminated

def remove_eliminated(votes, eliminated):
    for eliminated_option in eliminated:
        for vote in votes:
            try:
                vote.remove(eliminated_option)
            except e:
                pass                

def check_meets_quota(counted_votes, quota):
    for count in counted_votes.values():
        if count >= quota:
            return True
    return False

def reset_counted_votes(options):
    counted_votes = dict()
    for option in options:
        counted_votes[option] = 0
    return counted_votes

def build_count_str(votes):
    options = get_options(votes)
    num_options = len(options)
    page = "The options are " + str(options) + '<br>'
    page += "The votes are " + str(votes) + '<br>'
    page += "The number of votes is " + str(len(votes)) + '<br>'
    quota = int(len(votes)/2) + 1
    page += "The quota is " + str(quota) + '<br>'

    while(True):
        counted_votes = reset_counted_votes(options)

        for vote in votes:
            counted_votes[vote[0]] += 1
        page += "The current count is " + str(counted_votes) + '<br>'
        if check_meets_quota(counted_votes, quota):
            page += "Quota met" + '<br>'
            return page

        eliminated = find_eliminated(counted_votes)
        page += "The eliminated options are " + str(eliminated) + '<br>'

        remove_eliminated(votes, eliminated)
        options = get_options(votes)

        if len(votes[0]) <= 1:
            page += "All done" + '<br>'
            return page
    
        page += "The votes are " + str(votes) + '<br>' 
