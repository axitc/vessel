import requests
import json

import agent


def initresponsedict():
    responsedict = dict()
    responsedict['model'] = None
    responsedict['created_at'] = None
    responsedict['message'] = dict()
    responsedict['message']['role'] = 'assistant'
    responsedict['message']['content'] = ''
    responsedict['message']['thinking'] = ''
    return responsedict

def accumulateresponsedict(responsedict, linedict):
    responsedict['model'] = linedict['model']
    responsedict['created_at'] = linedict['created_at']
    if linedict['message']['content'] != '':
        responsedict['message']['content'] += linedict['message']['content']
    elif 'thinking' in linedict['message'] and linedict['message']['thinking'] != '':
        responsedict['message']['thinking'] += linedict['message']['thinking']
    elif 'tool_calls' in linedict['message']:
        if 'tool_calls' not in responsedict['message']:
            responsedict['message']['tool_calls'] = list()
        responsedict['message']['tool_calls'].append(linedict['message']['tool_calls'][0])
    return responsedict

def infer(model, tools, messages):
    url = 'http://127.0.0.1:11434/api/chat'
    headers = {'Content-Type':'application/json'}
    data = {
            'model':model,
            'messages':messages,
            'think':True,
            'stream':True,
            'tools':tools,
            #'options': {'num_thread': 6},
            }
    response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)
    responsedict = initresponsedict()  # to emulate simple inference (sinfer) dictionary to be returned, akin to non-streamed post request
    thinkingflag = False
    contentflag = False
    toolcallsflag = False
    for line in response.iter_lines():
        if not line:
            print('>>> NOT LINE')
        if line:
            decodedline = line.decode('utf-8')
            linedict = json.loads(decodedline)
            responsedict = accumulateresponsedict(responsedict, linedict)
            if 'thinking' in linedict['message'] and linedict['message']['thinking'] != '':
                if not thinkingflag:
                    print('\n\nAI - THINKING')
                    thinkingflag = True
                print(linedict['message']['thinking'], end='', flush=True)
            elif linedict['message']['content'] != '':
                if not contentflag:
                    print('\n\nAI - CONTENT')
                    contentflag = True
                print(linedict['message']['content'], end='', flush=True)
            elif 'tool_calls' in linedict['message']:
                if not toolcallsflag:
                    print('\n\nAI - TOOL CALLS')
                    toolcallsflag = True
                print(linedict['message']['tool_calls'][0]['function']['name'],'<-',linedict['message']['tool_calls'][0]['function']['arguments'])
    return responsedict

# infer, even though streamed, gives final output akin to sinfer ~ simple post request
def sinfer(model, tools, messages):
    url = 'http://127.0.0.1:11434/api/chat'
    headers = {'Content-Type':'application/json'}
    data = {
            'model':model,
            'messages':messages,
            'think':True,
            'stream':False,
            'tools':tools,
            #'options': {'num_thread': 6},
            }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    responsedict = response.json()
    return responsedict

def chat(model, tools, messages):
    while True:  # user-agent loop
        userprompt = input('\n\nUSER - PROMPT\n')
        messages.append({'role':'user','content':userprompt})
        while True:  # agent-environment loop
            responsedict = infer(model, tools, messages)
            if 'tool_calls' not in responsedict['message']:  # normal response for user
                messages.append({'role':'assistant','content':responsedict['message']['content']})
                break
            else:  # tool call
                messages.append({'role':'assistant','tool_calls':responsedict['message']['tool_calls']})
                toolresults = list()
                for toolcall in responsedict['message']['tool_calls']:
                    try:
                        toolresult = agent.executetoolcall(toolcall)
                    except Exception as e:
                        toolresult = 'ERROR: ' + str(e) + '\n'
                    toolresults.append(toolresult)
                print('\n\nENVIORNMENT - TOOL RESULTS')
                for i in range(len(toolresults)):
                    messages.append({'role':'tool','tool_name':responsedict['message']['tool_calls'][i]['function']['name'],'content':toolresults[i]})
                    print(responsedict['message']['tool_calls'][i]['function']['name'],'->',toolresults[i])

def main():
    model = agent.model
    tools = agent.tools
    messages = [{'role':'system','content':agent.systemprompt}]
    chat(model, tools, messages)

if __name__=='__main__':
    main()
