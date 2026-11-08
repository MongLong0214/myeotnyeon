"""LF2 correction: perform the unchanged audio, using its reviewed word cuts.

Original sources live in fix_evidence for comparison. No speech generation or
new alignment estimate is involved. Adjacent redundant crops are joined below.
"""
import copy,json,re
from pathlib import Path
P=Path(__file__).resolve().parent
D=json.loads((P/'fix_evidence/original_episode_data.json').read_text())
original=copy.deepcopy(D['shots']);shots=copy.deepcopy(original)
def actor(role,x,y=890,scale=1,view='three-quarter',**kw):
 return dict(id=kw.pop('id',role),role=role,x=x,y=y,scale=scale,view=view,**kw)
def prop(kind,x,y,scale=1,**kw):return dict(kind=kind,x=x,y=y,scale=scale,**kw)
def scene(n,room,layout,actors,props=(),foreground=None,place='',date='',description='',hold=''):
 s=shots[n-1];s.pop('match',None)
 s.update(set=room,action='reaction' if hold else 'performance',character_acting=True,subject=description.split('。')[0],depiction=description,illustrative=False,camera='snap',energy=0)
 s['performance']=dict(room=room,layout=layout,actors=actors,props=list(props),foreground=foreground,place=place,date=date,clock=s['start'],duration=s['end']-s['start'])
 # Legacy picture grammar is no longer an alternative source of truth.
 s['staging']=dict(sceneId=f'{room}_{layout}',clockStart=s['start'],actors=[],props=[],links=[],angleDeg={'side':70,'reverse':-70,'front':0,'wide':0}.get(layout,35),axis='대화의 시선축 유지; 프로필·뒷모습은 별도 도형',focus=dict(x=960,y=480,zoom=1))
 s['type']='medium' if room=='court' and layout=='front' else 'wide'
 if hold:s['motivated_hold']=hold
 return s

def interview(n,who='defendantB',view='side',description='',gesture='explain',place='조사실'):
 # The person giving a statement and the listener occupy opposite sides of
 # the table. Reverse shots redraw the near person from the back.
 if view=='reverse':
  aa=[actor('detective',430,950,1.12,'back',head=[0,8],right=[85,-240],rightTo=[115,-270],item='paper'),actor(who,1360,880,1.08,'three-quarter',flip=True,right=[85,-180],rightTo=[135,-280],head=[0,-7],talk=True)]
 else:
  aa=[actor('detective',480,880,1.04,'profile',right=[110,-265],rightTo=[140,-305],item='paper',head=[0,8]),actor(who,1420,890,1.1,'profile',flip=True,right=[100,-170],rightTo=[145,-280] if gesture=='explain' else [65,-240],head=[0,10] if gesture=='deny' else [8,0],talk=True)]
 return scene(n,'investigation',view,aa,foreground='desk',place=place,description=description)

def lab(n,description,layout='side',item='swab',operation='lift',place='감식실',date=''):
 aa=[actor('analyst',620 if layout!='reverse' else 1360,880,1.1,'profile' if layout!='reverse' else 'three-quarter',flip=layout=='reverse',right=[125,-130] if operation=='lift' else [115,-270],rightTo=[145,-290] if operation=='lift' else [170,-250],item=item,head=[5,16],gaze=[9,14])]
 if operation=='compare':aa.append(actor('detective',350,920,.98,'back',right=[85,-185],rightTo=[95,-255],head=[0,11]))
 pp=[prop('tray',900,712,.7),prop('microscope',1080,674,.72),prop('monitor',1350 if layout!='reverse' else 640,624,.87)]
 return scene(n,'lab',layout,aa,pp,foreground='lab',place=place,date=date,description=description)

def court(n,view,description,who='defendantB',date='',place='법정',gesture='read'):
 if view=='wide':
  aa=[actor('judge',960,575,.63,'front',right=[80,-260],rightTo=[100,-290],item='paper',head=[10,0]),actor('lawyer',330,900,.92,'profile',right=[110,-230],rightTo=[140,-300],item='paper'),actor('defendantA',1270,895,.9,'back',head=[0,7]),actor('defendantB',1540,895,.9,'back',head=[0,9])]
  fg='bench'
 elif view=='front':
  aa=[actor('judge',960,900,1.25,'front',right=[90,-280],rightTo=[130,-260],left=[-90,-255],leftTo=[-110,-278],item='paper' if gesture!='law' else 'book',head=[13,0],gaze=[-4,9],expression='firm')];fg='bench'
 elif view=='side':
  aa=[actor('lawyer',560,900,1.13,'profile',right=[100,-265],rightTo=[160,-307],item='paper' if gesture!='law' else 'book',head=[10,0]),actor('judge',1500,760,.76,'profile',flip=True,right=[85,-250],head=[0,10],item='paper')];fg=None
 else:
  aa=[actor('lawyer',280,980,1.27,'back',head=[0,6],right=[80,-260],rightTo=[110,-280],item='paper'),actor(who,1110,900,1.12,'profile',flip=True,right=[75,-180],rightTo=[110,-245] if gesture=='deny' else [75,-180],head=[0,15] if gesture!='deny' else [12,0],gaze=[8,14],talk=gesture=='deny'),actor('police',1650,895,.85,'profile',flip=True,right=[70,-195],head=[0,6])];fg='rail'
 s=scene(n,'court',view,aa,foreground=fg,place=place,date=date,description=description)
 s['staging']['sceneId']=f'court_{place}_{view}'
 return s

# Cold open. The firearm, collapse, and cash-bag departure are concrete actions.
scene(1,'garage','wide',[actor('robberA',530,875,1,'profile',right=[110,-260],rightTo=[190,-280],item='gun',head=[4,0],beat=[.05,.56]),actor('victim',1340,875,.95,'back',right=[85,-185],rightTo=[135,-245],head=[0,9],anonymous=True)], [prop('car',260,760,.8),prop('bag',1110,831,.7)],place='은행 지하',description='강도가 팔을 뻗어 권총을 겨누고 직원이 돌아본다. 총구 섬광은 원래 발화 시점에만 보인다.')
# Only this brief flash conveys firing; no wounds or bullet-count illustration.
shots[0]['performance']['fire']=dict(actor='robberA',start=31,end=34)
scene(2,'garage','side',[actor('robberA',470,875,.95,'profile',right=[190,-280],item='gun'),actor('victim',1350,870,.98,'back',fall=[0,1],beat=[.2,.8],anonymous=True)],[prop('car',200,740,.72),prop('bag',1160,810,.7,to=[1200,852],turn=40,beat=[.25,.8])],description='총격 뒤 익명의 출납과장이 바닥으로 쓰러지고 가방이 떨어진다.')
scene(3,'garage','side',[actor('employee',1710,880,.85,'profile',flip=True,to=[1480,880],run=True,right=[100,-180],rightTo=[160,-260]),actor('robberA',1080,880,.98,'profile',flip=True,to=[570,880],run=True,item='bag',right=[100,-165]),actor('robberB',620,880,.87,'profile',flip=True,to=[290,880],run=True,right=[100,-270])],[prop('car',270,745,.86)],description='복면 강도가 돈가방 하나를 들고 차로 달아나며 공범이 앞선다.')
lab(4,'수사관이 보관 마스크를 집어 관찰하고 감식 담당자 쪽으로 시선을 옮긴다.',item='mask')
lab(5,'보관된 마스크를 감식대 위로 옮기는 분석관과 대조 자료를 살피는 수사관.',operation='compare',item='evidence',layout='reverse')
court(6,'reverse','B가 선고를 듣고 고개를 떨군다. 뒤의 법정은 결말을 예고한다.')
scene(7,'garage','wide',[actor('employee',1320,875,.85,'profile',flip=True,to=[1150,875],item='bag'),actor('employee',1630,870,.73,'profile',flip=True,to=[1490,870],item='bag',id='staff2'),actor('victim',950,870,.83,'back',to=[875,860],anonymous=True)],[prop('car',1460,620,.7,truck=True)],place='대전 둔산동 · 은행 지하',date='2001-12-21',description='현금 운송차 옆에서 직원 세 명이 가방을 운반한다.')
scene(8,'garage','side',[actor('employee',1160,875,.94,'profile',flip=True,to=[1020,875],item='bag'),actor('employee',1510,875,.78,'profile',flip=True,to=[1380,875],item='bag',id='staff2'),actor('victim',790,870,.93,'back',to=[720,860],anonymous=True)],[prop('car',1550,660,.8,truck=True)],place='대전 둔산동 · 은행 지하',description='기둥 옆 측면 구도에서 가방을 든 직원들이 운반을 이어간다.')
scene(9,'garage','wide',[actor('employee',1210,875,.94,'profile',flip=True,to=[1060,875],item='bag'),actor('employee',1510,875,.82,'profile',flip=True,to=[1380,875],item='bag',id='staff2'),actor('victim',880,875,.95,'back',to=[780,875],anonymous=True)],[prop('car',1550,640,.8,truck=True)],description='세 직원 중 두 사람이 각각 가방을 들고 이동하고 출납과장이 앞선다.')
scene(10,'garage','reverse',[actor('victim',1200,890,1.07,'back',right=[80,-170],rightTo=[130,-250],head=[0,-10],anonymous=True),actor('employee',1640,870,.83,'profile',flip=True,item='bag',head=[0,-9])],[prop('car',780,760,1.05,to=[520,760],occupants=True)],description='직원들의 시선 앞으로 검은 승용차가 미끄러져 들어와 통로를 막는다.')
scene(11,'garage','side',[actor('robberA',560,875,1.03,'profile',to=[730,875],right=[80,-170],rightTo=[115,-240]),actor('robberB',320,880,.86,'three-quarter',to=[470,880]),actor('victim',1380,875,.94,'back',head=[0,-9],rightTo=[120,-260],anonymous=True)],[prop('car',270,750,.8)],description='차에서 나온 복면 두 사람이 직원에게 다가가고 직원이 그쪽을 본다.')
scene(12,'garage','reverse',[actor('robberA',730,880,1.18,'profile',right=[95,-180],rightTo=[175,-275],item='gun',beat=[.1,.82]),actor('victim',1540,960,1.2,'back',rightTo=[120,-265],anonymous=True)],[prop('car',350,720,.82)],description='직원 어깨 너머에서 강도가 권총을 들어 겨누는 행동을 보여준다.')
scene(13,'garage','side',[actor('victim',1240,860,.95,'back',fall=[1,1],anonymous=True),actor('employee',1530,885,.98,'profile',flip=True,right=[80,-155],rightTo=[145,-330],head=[0,14],expression='surprise')],[prop('car',330,730,.85),prop('bag',1070,837,.7)],description='쓰러진 익명 출납과장 쪽으로 동료가 손을 뻗다가 멈춘다. 상처 묘사는 없다.',hold='사망을 전하는 동안 구조적 동작을 멈추고 동료의 시선과 쓰러진 사람을 유지한다.')
scene(14,'memorial','side',[actor('employee',860,885,1.05,'profile',right=[110,-230],rightTo=[75,-190],head=[0,20],expression='sad')],[prop('chair',1300,690,.78),prop('coat',1310,527,.6)],description='빈 업무 의자 앞에서 동료의 손이 내려가고 시선이 멈춘다.',hold='일터의 상실을 말하는 감정 비트. 빈 의자와 동료의 시선을 고정한다.')
court(15,'front','판사가 기록을 읽고 고개를 들어 피해자에 관한 판단을 전한다.')
scene(16,'garage','wide',[actor('employee',700,890,1,'profile',item='bag',right=[110,-165],rightTo=[125,-195]),actor('employee',1390,890,1,'profile',flip=True,item='bag',right=[110,-165],rightTo=[125,-195],id='staff2')],[prop('car',1540,630,.76,truck=True)],description='두 직원이 각각 같은 크기의 돈가방을 들고 운반을 멈춘다.')
scene(17,'garage','side',[actor('robberA',900,885,1,'profile',flip=True,item='bag',right=[100,-170],to=[520,885],run=True),actor('employee',1530,885,.98,'profile',flip=True,item='bag',right=[100,-175],head=[0,-9]),actor('robberB',370,880,.8,'profile',flip=True,to=[220,880],run=True)],[prop('car',240,740,.72)],description='강도가 가방 하나를 들고 달아나고 다른 가방은 직원 손에 남는다.')
scene(18,'garage','reverse',[actor('employee',1440,890,1.07,'profile',flip=True,item='bag',right=[95,-180],head=[0,-10]),actor('robberA',630,880,.86,'profile',flip=True,item='bag',right=[100,-175],to=[240,880],run=True)],[prop('car',270,730,.74)],description='한 가방은 직원이 지키고 한 가방은 강도와 멀어진다. 총액·피해액은 자막으로만 구분한다.')
scene(19,'garage','wide',[actor('robberA',1190,880,1,'profile',flip=True,to=[990,880],right=[100,-160],rightTo=[150,-290])],[prop('car',740,745,1.13)],place='수원',description='훔칠 검은 승용차에 다가가는 익명 범인과 차의 넓은 측면.')
scene(20,'garage','side',[actor('robberA',1130,875,1,'profile',flip=True,to=[1000,875],right=[100,-175],rightTo=[160,-280])],[prop('car',740,745,1.13)],place='수원',date='2001-12-01',description='범인이 시동 중인 승용차 문 쪽으로 손을 뻗는다. 절도 방법은 추가하지 않는다.')
scene(21,'investigation','side',[actor('detective',630,895,1.12,'profile',right=[100,-240],rightTo=[155,-270],item='paper',head=[10,0]),actor('police',1450,890,.96,'profile',flip=True,head=[0,10])],[prop('gun',1130,691,.8),prop('file',905,714,.7)],foreground='desk',description='수사관이 차량 기록을 넘긴 뒤 수거된 권총을 살펴본다.')
scene(22,'investigation','reverse',[actor('detective',530,940,1.2,'back',right=[100,-245],rightTo=[140,-310],item='file'),actor('police',1430,885,1.08,'profile',flip=True,head=[0,13])],[prop('gun',1120,691,.8)],foreground='desk',description='기록을 펼친 수사관 너머로 경찰관이 권총 관련 자료를 내려다본다.')
scene(23,'street','wide',[actor('police',1100,885,1,'back',anonymous=True,to=[1000,880])],place='야간 순찰',date='2001-10-15',description='야간 거리를 순찰하던 익명 경찰관이 걸어간다.')
scene(24,'street','side',[actor('police',1090,885,1,'back',anonymous=True,fall=[0,1],beat=[.5,.95])],[prop('car',1650,790,1.04,to=[1160,790],beat=[0,.66],occupants=True)],description='차가 도보 순찰 경찰관 쪽으로 진행하고 충돌 뒤 경찰관이 쓰러진다. 고어는 없다.')
scene(25,'street','reverse',[actor('police',1100,880,.95,'back',anonymous=True,fall=[1,1]),actor('robberA',1530,890,.99,'profile',flip=True,right=[145,-125],rightTo=[145,-230],item='gun',head=[8,15])],[prop('car',640,735,.88,occupants=True)],description='쓰러진 경찰관 옆에서 범인이 빼앗은 권총을 들어 올린다.')
scene(26,'street','side',[actor('police',1120,870,.95,'back',anonymous=True,fall=[1,1]),actor('medic',1560,885,1,'profile',flip=True,to=[1430,885],right=[100,-170],rightTo=[155,-235],head=[0,18])],[prop('car',350,730,.85)],description='크게 다친 경찰관 곁으로 구조 인물이 다가가 상태를 살핀다. 사망 장치나 상처는 없다.')
scene(27,'street','reverse',[actor('police',1120,870,.95,'back',anonymous=True,fall=[1,1]),actor('medic',1440,885,1,'profile',flip=True,right=[155,-235],rightTo=[180,-230],head=[18,9])],[prop('car',350,730,.85)],description='구조자가 쓰러진 경찰관을 살피며 손을 뻗는다. 죽음으로 바꾸지 않는다.')
scene(28,'garage','side',[actor('robberA',740,890,1.12,'profile',right=[120,-220],rightTo=[180,-280],item='gun'),actor('employee',1560,890,1,'back',rightTo=[130,-250])],[prop('car',320,740,.82)],place='은행 지하',description='은행 지하에서 강도가 빼앗은 권총을 겨누고 직원이 반응한다.')
scene(29,'garage','wide',[actor('detective',760,890,1,'profile',right=[90,-180],rightTo=[160,-330],head=[0,-12]),actor('police',1480,890,.95,'profile',flip=True,head=[0,-12])],place='은행 지하',description='현장을 둘러보는 수사관이 카메라 없는 벽과 천장을 살피고 경찰관이 그 시선을 따른다.')
scene(30,'garage','wide',[],description='V6_029의 현장 확인 행동을 끊지 않고 유지한다.')
scene(31,'garage','wide',[actor('robberA',1270,890,.98,'profile',flip=True,to=[640,890],run=True,item='bag',right=[100,-170]),actor('robberB',1450,885,.86,'profile',flip=True,to=[820,885],run=True)],[prop('car',1510,680,.85),prop('car',400,745,.9)],place='인근 상가 지하',description='버려둘 차에서 다른 차로 가방을 든 두 범인이 이동한다.')
scene(32,'garage','reverse',[actor('robberA',570,890,.85,'profile',flip=True,to=[360,890],run=True,item='bag'),actor('robberB',810,890,1,'profile',flip=True,to=[570,890],right=[100,-220],rightTo=[100,-160])],[prop('car',1350,740,1.05),prop('mask',1190,690,.7),prop('cloth',1470,701,.7)],description='범인들이 떠나는 뒤쪽에 버려진 차와 마스크·손수건이 남는다.')
scene(33,'garage','side',[actor('robberB',1090,890,1.05,'profile',right=[100,-250],rightTo=[140,-190],head=[0,12],to=[1000,890]),actor('robberA',430,880,.88,'profile',flip=True,item='bag',to=[320,880])],[prop('car',1410,730,1)],description='범인이 버린 차 곁에 손을 뻗었다가 거둔다. 방화 시도는 작은 불빛만, 점화 방법·차량 전소는 그리지 않는다.')
shots[32]['performance']['fireAttempt']=True
lab(34,'감식 담당자가 남은 마스크를 들어 올려 수거 트레이 위에서 손수건과 함께 살핀다.',item='mask')
scene(35,'lab','side',[],description='V6_034의 수거물 확인을 유지한다.')
scene(36,'lab','reverse',[actor('host',1420,895,1.12,'profile',flip=True,right=[100,-245],rightTo=[160,-285],head=[0,12],gaze=[9,15]),actor('analyst',530,895,1,'back',right=[100,-250],rightTo=[150,-280],item='evidence')],[prop('tray',950,716,.8),prop('cloth',920,690,.65)],foreground='lab',description='진행자가 보관 마스크를 가리키고 분석관이 증거 봉투를 살핀다. 삭제 실패 판은 없다.')
scene(37,'garage','side',[actor('detective',730,890,1.1,'profile',right=[100,-160],rightTo=[145,-270],item='evidence',head=[10,0])],[prop('car',1320,730,1.02)],description='수사관이 버려진 차 옆에서 남은 천 조각이 든 증거 봉투를 들어 확인한다.')
lab(38,'분석관이 마스크를 검사하고 고개를 숙여 결과를 다시 읽는다.',operation='inspect',item='paper')
scene(39,'lab','side',[],description='V6_038의 검사와 결과 재확인 행동을 유지한다.')
lab(40,'분석관이 검출 결과에서 시선을 떼고 마스크가 든 증거 봉투로 손을 옮긴다.',layout='reverse',item='evidence',operation='inspect')
scene(41,'investigation','side',[actor('detective',650,895,1.12,'profile',right=[115,-280],rightTo=[95,-230],item='file',head=[0,17]),actor('clerk',1450,890,.98,'profile',flip=True,right=[90,-255],rightTo=[125,-260],item='evidence')],foreground='desk',description='마스크 증거와 신원 기록을 번갈아 본 수사관이 자료를 내려놓고 다시 확인한다. 이름을 얻지 못한 망설임이다.')
scene(42,'investigation','wide',[actor('clerk',1230,885,1.02,'profile',flip=True,to=[1090,885],right=[105,-220],rightTo=[130,-165],item='evidence'),actor('detective',680,895,1,'profile',right=[105,-230],rightTo=[145,-190],item='file')],[prop('box',1110,731,.72)],place='둔산경찰서',description='담당자가 마스크·손수건 봉투를 보관 상자로 옮기고 수사관이 인수 기록을 정리한다.')
scene(43,'investigation','wide',[actor('detective',550,895,1.05,'profile',right=[110,-270],rightTo=[150,-290],item='file',head=[0,12]),actor('clerk',1380,895,1.03,'profile',flip=True,right=[110,-275],rightTo=[145,-225],item='paper',head=[10,0]),actor('clerk',1710,880,.82,'back',id='clerk2',right=[90,-210],rightTo=[120,-270],item='file')],[prop('box',1050,745,.65)],foreground='desk',description='여러 수사자가 진술 기록과 차량 조사 기록을 넘겨가며 대조한다. 조사 수치는 기존 자막에서만 읽힌다.')
scene(44,'investigation','reverse',[actor('detective',520,950,1.16,'back',right=[100,-260],rightTo=[85,-200],item='paper',head=[0,15]),actor('clerk',1410,890,1.08,'profile',flip=True,right=[110,-270],rightTo=[120,-230],item='file',head=[0,15])],foreground='desk',description='서류를 넘긴 손이 멈추고 수사자들이 서로 바라본다. 신원을 못 찾은 조사 반응이다.')
scene(45,'court','wide',[actor('clerk',680,895,.9,'back',anonymous=True),actor('clerk',1050,895,.9,'back',anonymous=True,id='other2'),actor('clerk',1420,895,.9,'back',anonymous=True,id='other3'),actor('judge',960,575,.63,'front',right=[80,-260],rightTo=[110,-280],item='file',head=[12,0])],foreground='bench',date='2002',description='A·B와 다른 익명 용의자 세 명이 재판부 앞에 서고 판사가 서류를 확인한다.')
court(46,'front','판사가 영장 서류를 읽고 내려놓는다. 기각 결론은 변함없는 자막으로 전달한다.')
scene(47,'court','reverse',[actor('clerk',1110,895,1.05,'profile',flip=True,anonymous=True,to=[1000,895],head=[8,0]),actor('clerk',1440,895,.98,'back',anonymous=True,id='other2',to=[1350,895]),actor('clerk',1690,895,.88,'back',anonymous=True,id='other3',to=[1620,895])],place='2002년 영장 심사',description='다른 용의자 세 명을 뒷모습과 별도 복장으로 보여준다. A·B의 도형을 재사용하지 않는다.')
shots[46]['performance']['place']='영장 심사'
scene(48,'investigation','wide',[actor('clerk',1380,890,1.04,'profile',flip=True,right=[120,-240],rightTo=[170,-250],item='file'),actor('detective',650,890,1.08,'profile',right=[110,-190],rightTo=[170,-240],left=[-90,-250],leftTo=[-120,-260],leftItem='evidence')],[prop('box',1080,727,.8)],date='2011-12',place='중요미제 전담수사팀',description='이전 담당자가 기록을 건네고 전담 수사자가 서류와 보관 증거를 인수한다.')
scene(49,'investigation','side',[actor('detective',630,895,1.1,'profile',right=[110,-280],rightTo=[145,-300],item='book',head=[8,0]),actor('clerk',1420,895,1.02,'profile',flip=True,right=[110,-260],rightTo=[145,-225],item='file')],foreground='desk',date='2015',description='법 개정 자료를 읽은 수사관이 진행 중인 사건 기록으로 고개를 돌린다. 법률 도식은 없다.')
scene(50,'investigation','reverse',[actor('detective',530,940,1.16,'back',right=[100,-230],rightTo=[150,-275],item='file'),actor('clerk',1390,890,1.07,'profile',flip=True,right=[110,-240],rightTo=[150,-280],item='paper',head=[0,10])],foreground='desk',description='수사팀이 사건 기록을 다시 펼치고 다음 조사 자료를 건넨다.')
lab(51,'보관 증거를 감식대에 올리고 면봉을 들어 재감식을 시작한다.',date='2017')
lab(52,'마스크·손수건 채취물을 검사대에서 다루고 분석 화면을 확인한다.',layout='reverse',item='evidence',operation='compare')
lab(53,'화면을 본 분석관이 뒤의 수사관에게 고개를 돌리고 비교 자료를 요청하는 손짓을 한다.',layout='side',item='paper',operation='compare')
scene(54,'investigation','side',[actor('detective',700,890,1.12,'profile',right=[110,-245],rightTo=[160,-270],item='file',head=[9,0]),actor('clerk',1450,890,1.03,'profile',flip=True,right=[100,-230],rightTo=[140,-275],item='paper')],foreground='desk',description='수사관이 은행 기록을 닫고 별도의 수거물 기록으로 손을 옮긴다.')
scene(55,'arcade','wide',[actor('police',790,890,1.08,'profile',right=[110,-155],rightTo=[145,-245],item='cigarette',head=[0,17]),actor('clerk',1400,895,1.03,'profile',flip=True,right=[110,-235],rightTo=[155,-240],item='evidence')],[prop('tray',1050,752,.6)],place='충북 · 불법게임장',date='2015',description='게임기 사이에서 수거자가 담배꽁초를 집어 증거 봉투 쪽으로 옮긴다.')
lab(56,'분석관이 두 수거물의 분석 화면을 번갈아 지목하고 수사관이 같은 위치의 띠를 확인한다.',operation='compare',item='swab')
lab(57,'분석관이 마스크·손수건 봉투와 담배꽁초 봉투를 같은 트레이 위에 모아 놓는다.',layout='reverse',item='evidence',operation='lift')
lab(58,'수사관이 비교 결과 쪽으로 몸을 돌리고 분석관이 화면의 일치 위치에 손을 뻗는다.',operation='compare',item='paper')
scene(59,'lab','reverse',[actor('host',1370,895,1.12,'profile',flip=True,right=[100,-200],rightTo=[160,-280],head=[0,12]),actor('analyst',550,890,1.02,'back',right=[110,-260],rightTo=[145,-280],item='evidence')],[prop('tray',960,714,.75),prop('cigarette',950,686,.55)],foreground='lab',description='진행자가 버린 물건을 가리킨 뒤 분석관이 든 봉투로 시선을 옮긴다.')
scene(60,'investigation','side',[actor('detective',620,890,1.1,'profile',right=[110,-270],rightTo=[100,-230],item='file',head=[0,14]),actor('analyst',1430,890,1.03,'profile',flip=True,right=[110,-265],rightTo=[155,-265],item='paper')],foreground='desk',description='분석관이 결과를 건네도 수사관은 신원 기록을 다시 넘겨본다. 자동으로 이름이 생기지 않는다.')
lab(61,'분석관이 신원 정보 없는 수거물 봉투를 확인하고 수사관 쪽으로 건넨다.',layout='reverse',item='evidence',operation='compare')
scene(62,'investigation','wide',[actor('detective',650,890,1.08,'profile',right=[110,-250],rightTo=[150,-280],item='file',head=[0,10]),actor('clerk',1410,890,1.04,'profile',flip=True,right=[110,-270],rightTo=[160,-235],item='paper')],[prop('box',1060,740,.7)],foreground='desk',description='일치 결과를 옆에 둔 채 수사자들이 다른 신원 기록을 넘기며 확인을 계속한다.')
scene(63,'arcade','side',[actor('detective',630,890,1.1,'profile',right=[110,-240],rightTo=[145,-285],item='file'),actor('clerk',1400,890,1.08,'profile',flip=True,right=[110,-175],rightTo=[155,-255],head=[0,10],talk=True)],description='게임장 출입 가능자를 확인하는 수사관이 관계자의 설명을 들으며 기록한다.')
scene(64,'investigation','reverse',[actor('detective',480,940,1.18,'back',right=[100,-250],rightTo=[155,-260],item='paper'),actor('clerk',1420,895,1.07,'profile',flip=True,right=[110,-260],rightTo=[145,-240],item='file',head=[0,12])],foreground='desk',description='수사자들이 명단과 출입 기록을 대조한다. 전원 DNA 채취 장면은 그리지 않는다.')
scene(65,'investigation','side',[actor('detective',650,895,1.12,'profile',right=[110,-280],rightTo=[160,-260],item='paper',head=[8,0]),actor('clerk',1430,890,1.03,'profile',flip=True,right=[110,-245],rightTo=[155,-285],item='file')],foreground='desk',description='몽타주가 포함된 기록과 목격 진술·차량 기록을 번갈아 대조한다.')
scene(66,'investigation','wide',[actor('detective',650,890,1.08,'profile',right=[110,-245],rightTo=[160,-280],item='file'),actor('clerk',1410,890,1.03,'profile',flip=True,right=[110,-270],rightTo=[145,-240],item='paper')],[prop('box',1060,740,.7)],foreground='desk',description='수사관이 대조한 기록 한 묶음을 옆으로 밀고 다음 기록을 받아 재확인한다.')
scene(67,'investigation','reverse',[actor('detective',510,940,1.17,'back',right=[100,-235],rightTo=[155,-280],item='file'),actor('clerk',1420,890,1.08,'profile',flip=True,head=[0,9],right=[110,-250],rightTo=[145,-275],item='paper')],foreground='desk',date='2022-03',description='특정한 용의자 기록을 펼친 수사관이 담당자와 대조 결과를 확인한다.')
scene(68,'investigation','side',[actor('detective',720,895,1.17,'profile',right=[110,-260],rightTo=[95,-225],item='file',head=[0,13])],foreground='desk',description='B의 기록을 내려놓은 뒤 수사관이 남은 공범 자료로 시선을 돌린다.')
scene(69,'investigation','wide',[actor('detective',650,890,1.08,'profile',right=[110,-255],rightTo=[145,-280],item='file'),actor('clerk',1400,890,1.04,'profile',flip=True,right=[110,-170],rightTo=[155,-250],talk=True)],foreground='desk',description='수사관이 주변인 설명을 들으며 과거 행적 기록을 넘긴다.')
scene(70,'street','wide',[actor('detective',550,890,1.06,'profile',to=[860,890],right=[100,-180],rightTo=[170,-250]),actor('defendantB',1360,890,1.04,'profile',flip=True,head=[0,13],right=[80,-180],rightTo=[105,-225])],place='대전',date='2022-08-25',description='수사관이 B에게 다가가 체포를 집행하고 B가 몸을 돌린다.')
scene(71,'street','reverse',[actor('detective',800,895,1.08,'back',to=[690,895],right=[120,-230]),actor('defendantB',1230,895,1.08,'profile',flip=True,to=[1110,895],head=[8,0])],place='대전',description='체포된 B와 수사관이 같은 방향으로 이동한다.')
interview(72,description='B가 조사관에게 손을 펴 진술하고 조사관이 그 말을 기록한다.')
interview(73,view='reverse',description='B가 설명을 마치자 조사관이 다른 자료를 들어 확인한다.')
scene(74,'investigation','side',[actor('detective',680,895,1.13,'profile',right=[110,-255],rightTo=[155,-285],item='paper',head=[5,0]),actor('clerk',1430,890,1.04,'profile',flip=True,right=[110,-265],rightTo=[145,-240],item='file')],foreground='desk',description='조사관이 진술서를 확인한다. A의 DNA를 직접 대조하는 그림은 쓰지 않는다.')
scene(75,'spa','wide',[actor('detective',600,890,1.08,'profile',to=[900,890],right=[100,-175],rightTo=[170,-245]),actor('defendantA',1420,890,1.05,'profile',flip=True,head=[0,12],rightTo=[110,-225])],place='강원 정선 · 찜질방',description='찜질방에서 수사관이 A에게 다가가 체포를 집행한다.')
scene(76,'investigation','wide',[actor('detective',640,890,1.08,'profile',right=[110,-260],rightTo=[145,-280],item='file'),actor('clerk',1410,890,1.04,'profile',flip=True,right=[110,-260],rightTo=[155,-240],item='paper')],foreground='desk',description='수사관들이 두 사람의 과거 기록을 대조한다. 학생 시절의 사건이나 얼굴은 창작하지 않는다.')
court(77,'wide','두 피고인이 재판부 앞에 서고 판사가 구속 관련 기록을 확인한다.',date='2022-08-27',place='구속 절차')
scene(78,'investigation','reverse',[actor('detective',510,940,1.16,'back',right=[100,-245],rightTo=[140,-280],item='file'),actor('clerk',1400,890,1.07,'profile',flip=True,right=[110,-260],rightTo=[145,-230],item='paper',head=[0,10])],foreground='desk',description='오래된 기록을 덮고 검거 기록으로 바꾸는 수사관의 손과 이를 확인하는 동료.')
scene(79,'investigation','wide',[actor('clerk',1380,890,1.04,'profile',flip=True,right=[110,-220],rightTo=[140,-270],item='file'),actor('detective',650,890,1.09,'profile',right=[110,-230],rightTo=[145,-265],item='file')],[prop('box',1030,747,.72)],foreground='desk',description='쌓인 수사기록에서 두 담당자가 묶음을 꺼내 확인한다. 권수·상자 수는 수치로 단정하지 않는다.')
scene(80,'investigation','side',[actor('host',680,895,1.15,'profile',right=[110,-235],rightTo=[155,-280],head=[0,10]),actor('detective',1420,890,1.04,'profile',flip=True,right=[110,-260],rightTo=[145,-225],item='file')],foreground='desk',description='진행자가 기록 더미를 가리키고 실제로 기록을 넘기는 수사자에게 고개를 돌린다.')
court(81,'wide','두 피고인이 법정에 서고 상대 쪽으로 고개를 돌린다.')
interview(82,'defendantA','side','A가 상대 방향으로 손을 뻗으며 책임을 돌리는 진술을 한다.',place='진술 재구성')
interview(83,'defendantB','reverse','반대편에서 B가 손을 뻗어 자기 진술을 하고 조사관이 듣는다.',place='진술 재구성')
interview(84,'defendantA','side','조사관이 A의 진술서를 다시 확인하고 A가 시선을 내려 답한다. 경찰 발표 내용은 자막으로 구분한다.')
court(85,'reverse','A가 법정에서 손을 들어 부인하고 재판부 방향을 본다.',who='defendantA',gesture='deny')
interview(86,description='B가 돈 분배 관련 진술을 하고 조사관이 진술서를 읽는다.')
interview(87,view='reverse',description='B가 손을 펴 분배 내용을 설명하고 조사관이 기록한다. 금액은 B의 진술 자막으로만 전한다.')
interview(88,'defendantA','side','A가 별도 조사 장면에서 양손을 펴 자신의 분배 주장을 말한다.')
scene(89,'investigation','wide',[actor('detective',610,890,1.1,'profile',right=[110,-260],rightTo=[155,-285],item='paper',left=[-90,-240],leftTo=[-125,-275],leftItem='file'),actor('clerk',1420,890,1.05,'profile',flip=True,head=[0,12])],foreground='desk',description='수사관이 서로 다른 두 진술서를 번갈아 들어 대조한다. 현금 분배를 사실처럼 재연하지 않는다.')
scene(90,'investigation','wide',[],description='V6_089의 두 진술서 대조를 끊지 않고 유지한다.')
scene(91,'investigation','reverse',[actor('detective',510,940,1.17,'back',right=[110,-260],rightTo=[150,-280],item='paper',left=[-90,-240],leftTo=[-120,-260],leftItem='file'),actor('clerk',1410,890,1.07,'profile',flip=True,right=[110,-260],rightTo=[145,-245],item='paper',head=[0,12])],foreground='desk',description='두 장의 다른 진술을 동료와 확인하고 시선을 교환한다.')
scene(92,'investigation','side',[actor('host',680,895,1.15,'profile',right=[100,-190],rightTo=[155,-265],head=[0,10]),actor('detective',1430,890,1.04,'profile',flip=True,right=[110,-260],rightTo=[150,-245],item='paper')],foreground='desk',description='진행자가 한 진술서에서 다른 진술서로 손을 옮기며 책임 전가를 논평한다.')
court(93,'reverse','피고인 A가 상대 방향으로 손을 들어 총격 책임을 부인한다.',who='defendantA',gesture='deny')
court(94,'side','검사가 재판부를 향해 서면을 들어 구형하고 판사는 이를 듣는다.',date='2023-01-16',place='검찰 구형')
court(95,'front','검사의 요구를 듣는 판사가 구형 서류를 내려다본다. 선고 동작으로 꾸미지 않는다.')
court(96,'reverse','A가 검사 쪽을 향해 짧게 몸과 고개를 숙인다. 보도된 발언의 취지만 자막으로 전달한다.',who='defendantA',gesture='deny')
scene(97,'court','side',[actor('clerk',650,890,1.12,'profile',right=[110,-260],rightTo=[150,-280],item='paper',left=[-90,-240],leftTo=[-125,-270],leftItem='file',head=[0,12])],foreground='desk',place='공판 기록',description='서로 다른 보도·기록을 대조하는 담당자의 손을 보여준다. 합성 인용문은 없다.')
court(98,'front','판사가 진술 기록을 읽고 고개를 들어 판단할 대상을 본다.')
court(99,'reverse','A가 판사 방향의 시선을 유지하고 손을 내려놓는다. 발사자 판단을 앞둔 청취 반응.',who='defendantA')
court(100,'side','검사가 B 관련 서면을 들어 재판부에 제시하고 판사가 자료를 본다.')
court(101,'wide','판사가 A·B에게 1심 선고를 읽고 두 피고인이 이를 듣는다. 형량 설명판은 없다.',date='2023-02-17',place='1심 선고')
court(102,'reverse','A가 재판부 쪽을 보다가 시선을 내린다. 법원이 인정한 총격 책임은 자막으로 전달한다.',who='defendantA')
court(103,'side','검사가 증거 기록을 펼치며 다른 판단 근거로 손을 옮긴다.')
court(104,'front','판사가 권총 취급 정황과 진술 기록을 번갈아 읽고 고개를 든다.')
court(105,'reverse','B가 자신의 진술 기록을 든 변호인 쪽으로 고개를 돌린다.')
interview(106,'defendantB','side','수사 단계의 B 진술 장면으로 돌아가 조사관이 기록을 확인하고 B가 설명한다.')
court(107,'wide','항소심 재판부·검사·두 피고인을 새 설정 숏으로 보여준다.',place='항소심')
court(108,'reverse','B가 법정의 설명을 들으며 고개를 든다.')
court(109,'side','검사가 판결 관련 서면을 들어 설명하고 B 쪽으로 시선을 옮긴다.')
court(110,'wide','항소심 재판부가 두 피고인에게 선고하고 모두 재판부를 바라본다.',date='2023-08-18',place='항소심 선고')
court(111,'reverse','B가 선고를 듣고 고개를 내린다. 20년에서 무기로 바뀐 결과는 자막이 전한다.')
court(112,'side','검사가 적용법 책을 펴 재판부 쪽에 보여주고 판사가 그 자료를 본다.',gesture='law')
court(113,'front','판사가 적용법을 읽은 뒤 피고인 쪽으로 고개를 든다. 법정형은 기존 자막만 쓴다.',gesture='law')
court(114,'side','법 책을 펼친 변호인이 감경 범위 부분을 짚고 재판부의 반응을 기다린다.',gesture='law')
court(115,'front','판사가 1심 기록과 적용법을 확인하고 기록을 내려놓는다.')
court(116,'reverse','B가 설명을 들으며 다시 재판부를 쳐다본다. 감경 여부를 기다리는 청취 반응.')
court(117,'front','판사가 양형 기록을 읽고 손을 내려 감경하지 않는 판단을 전한다.')
court(118,'side','변호인이 법 책에서 시선을 떼고 선고를 듣는다.',gesture='law')
court(119,'reverse','B가 선고를 듣고 시선을 내린 채 손을 내려놓는다.')
scene(120,'court','side',[actor('host',650,895,1.15,'profile',right=[110,-230],rightTo=[160,-280],head=[0,10]),actor('lawyer',1440,890,1.03,'profile',flip=True,right=[110,-270],rightTo=[150,-240],item='book')],description='진행자가 법 책을 보는 변호인을 향해 손짓한다. 숫자 표나 화살표는 없다.')
court(121,'reverse','B가 판결을 듣는 청취 모습. B를 총을 든 사람으로 바꾸어 그리지 않는다.')
court(122,'front','판사가 A 쪽으로 시선을 옮겨 기존 총격 판단을 확인한다.')
scene(123,'court','wide',[actor('defendantA',690,895,1.04,'profile',right=[90,-190],rightTo=[125,-260],head=[0,10]),actor('defendantB',1120,895,1.04,'profile',flip=True,right=[90,-190],rightTo=[125,-260],head=[0,10]),actor('lawyer',1570,890,.98,'profile',flip=True,right=[110,-245],rightTo=[150,-280],item='paper')],description='두 피고인이 변호인에게 상고 서면을 확인하고 변호인이 이를 들어 읽는다.')
scene(124,'court','reverse',[actor('lawyer',660,890,1.13,'profile',right=[110,-260],rightTo=[145,-280],item='file',to=[850,890]),actor('clerk',1440,890,1.03,'profile',flip=True,right=[110,-220],rightTo=[155,-260])],place='대법원',description='대법원 심리 단계에서 서면을 든 법률가가 기록을 전달한다.')
court(125,'front','대법원 재판부가 기록을 읽고 마지막 서면으로 손을 옮긴다.',place='대법원')
court(126,'wide','대법원 재판부가 상고기각 결론을 읽고 법정 인물들이 이를 듣는다.',date='2023-12-14',place='대법원')
court(127,'reverse','피고인이 최종 판단을 듣고 고개를 내린다. 확정 형량은 자막에만 나온다.')
court(128,'front','재판부가 원심 양형 기록을 덮고 피고인 쪽을 바라본다.')
scene(129,'investigation','side',[actor('lawyer',640,895,1.13,'profile',right=[110,-260],rightTo=[150,-280],item='book',head=[0,10]),actor('host',1440,890,1.04,'profile',flip=True,right=[95,-180],rightTo=[130,-240],head=[8,0])],foreground='desk',description='법 책을 펼친 법률가가 형의 의미를 설명하고 진행자가 듣는다. 출소 불가 도식이나 가석방 결과는 만들지 않는다.')
scene(130,'memorial','wide',[actor('employee',900,890,1.05,'profile',right=[100,-180],rightTo=[130,-200],item='flowers',head=[0,17],expression='sad')],[prop('chair',1400,700,.85),prop('coat',1410,517,.65)],description='동료가 빈 업무 의자 앞에서 꽃을 들고 멈춘다. 유족 얼굴·나이는 만들지 않는다.',hold='두 자녀를 둔 가장의 상실을 전하는 동안 빈 의자 앞에 멈춘 동료를 유지한다.')
scene(131,'investigation','side',[actor('police',650,895,1.1,'profile',right=[110,-265],rightTo=[150,-280],item='paper',head=[0,10]),actor('clerk',1420,890,1.03,'profile',flip=True,right=[110,-245],rightTo=[145,-260],item='file')],foreground='desk',place='경찰을 통한 전언',description='경찰이 기록된 메시지의 취지를 담당자에게 전하고 담당자가 자료를 확인한다. 유족 인터뷰나 전화 녹음은 재현하지 않는다.')
scene(132,'memorial','side',[actor('employee',880,890,1.09,'profile',right=[120,-205],rightTo=[165,-215],item='flowers',head=[16,20],expression='sad')],[prop('chair',1380,700,.86),prop('coat',1390,519,.64)],description='동료가 꽃을 든 손을 빈 의자 쪽으로 옮긴 뒤 멈춘다. 범인 얼굴 대신 일터를 본다.',hold='결말의 초점을 피해자의 빈 일자리로 옮기는 정지. 슬픔을 꾸미는 반복 동작을 넣지 않는다.')
scene(133,'memorial','side',[],description='V6_132의 빈 일자리와 동료의 시선을 마지막 발화까지 유지한다.')

# The final act is allowed to settle rather than restarting an idle cycle.
shots[131]['performance']['actors'][0]['beat']=[.04,.37]
# Numeric dates change presentation only. Unknown month/day components stay
# absent; durations such as 20년 8개월 and sentence lengths are untouched.
def numeric_dates(text):
 text=re.sub(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',lambda m:f'{m[1]}-{int(m[2]):02}-{int(m[3]):02}',text)
 text=re.sub(r'(\d{4})년\s*(\d{1,2})월',lambda m:f'{m[1]}-{int(m[2]):02}',text)
 return re.sub(r'(\d{4})년',r'\1',text)
for s in shots:
 s['performance']['place']=numeric_dates(s['performance']['place'])
 s['performance']['place']={'야간 순찰':'거리','중요미제 전담수사팀':'수사실','구속 절차':'법정','진술 재구성':'조사실','검찰 구형':'법정','공판 기록':'법정','1심 선고':'대전지법','항소심':'대전고법','항소심 선고':'대전고법','경찰을 통한 전언':'경찰서'}.get(s['performance']['place'],s['performance']['place'])
 s['sourceShots']=[s['id']]
 s['screen_direction']='대화 시선축 유지; 차량·도주 우→좌'
 s['axis_side']='A'
# Same information, same action: no additional crop or reset at these old cuts.
merges={26:27,29:30,34:35,38:39,89:90,132:133}
for first,last in merges.items():
 a,b=shots[first-1],shots[last-1]
 a['end']=b['end'];a['performance']['duration']=a['end']-a['start']
 a['sourceShots']=[x['id'] for x in shots[first-1:last]]
 a['purpose']=' '.join(x['purpose'] for x in shots[first-1:last])
 a['facts']=list(dict.fromkeys(f for x in shots[first-1:last] for f in x['facts']))
 a['depiction']+=' 기존 후속 확대 컷을 합치고 행동·시선을 유지한다.'
shots=[s for i,s in enumerate(shots,1) if i not in merges.values()]
for i,s in enumerate(shots):s['index']=i
D['shots']=shots
for c in D['captions']:c['text']=numeric_dates(c['text'])
(P/'episode_data.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')))
(P/'shots_v6.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2)+'\n')
(P/'captions.json').write_text(json.dumps(D['captions'],ensure_ascii=False,indent=2)+'\n')
def stamp(ms):
 ms=round(ms);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(P/'subtitles.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['startMs'])} --> {stamp(c['endMs'])}\n{c['text']}" for i,c in enumerate(D['captions']))+'\n')
md=['# LF2 v6 correction · 내레이션–화면 정합표','','대본·TTS는 원본 바이트를 유지한다. 날짜는 표시만 수치화한다. 원본 133개 숏 중 정보 없는 후속 확대·반복 6개를 합쳤다. 나머지 컷은 같은 절 경계다. 제작 쪽 MATCH를 기록하지 않으며 최종 판단은 별도 검수다.','','| 숏(원본 대응) | 시작–끝 (초) | 변경 없는 내레이션 | 실제 행동·시선·반응 | 구도 | 검토 상태 |','|---|---|---|---|---|---|']
for s in shots:md.append(f"| {', '.join(s['sourceShots'])} | {s['start']/30:.3f}–{s['end']/30:.3f} | {s['purpose']} | {s['depiction']} | {s['performance']['room']} / {s['performance']['layout']}; 옆얼굴·뒷모습 별도 도형 | CEO 재검수 대기 |")
md+=['','## 컷 경계 변경','',*['- '+shots_id+'의 시작 컷 제거; 앞 숏의 행동·시선 연속 유지.' for shots_id in [f'V6_{i:03}' for i in merges.values()]],'','새 위치로 옮긴 컷은 없다. 삭제된 컷 이외 모든 시작 프레임은 원본 단어·절 경계와 동일하다.']
(P/'alignment.md').write_text('\n'.join(md)+'\n')
assert [(n['text']) for n in D['narration']]==[n['text'] for n in json.loads((P/'fix_evidence/original_episode_data.json').read_text())['narration']]
assert (P/'script_v2.md').read_bytes()==(P/'fix_evidence/original_script_v2.md').read_bytes()
print(f'{len(shots)} performed shots; {len(merges)} redundant cuts removed; script/audio untouched')
