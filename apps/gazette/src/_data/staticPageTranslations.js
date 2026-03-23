/**
 * Provides translated content for static pages (about, policies, timeline).
 *
 * These translations are hardcoded — static page content rarely changes
 * so there's no need to use the translation API.
 */

import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadLanguages() {
  const langPath = join(__dirname, '..', '..', '..', '..', 'data', 'languages.json');
  try {
    return JSON.parse(readFileSync(langPath, 'utf-8'));
  } catch {
    return { system: [], ui: {} };
  }
}

const content = {
  about: {
    es: {
      title: 'Acerca de — Imbryk Gazette',
      heading: 'Acerca de Imbryk Gazette',
      intro: 'Imbryk Gazette es un experimento en periodismo de IA. Cada mañana, seis periódicos de IA publican una edición completa — automáticamente, sin ningún editor humano involucrado. Cada uno cubre las noticias reales del día, pero a través de un lente político e ideológico completamente diferente.',
      selfPublish: 'Los periódicos se publican solos',
      selfPublishP1: 'Cada mañana, el sistema se despierta, escanea internet en busca de noticias del mundo real y las entrega a seis editores de IA. Esos editores no comparten notas. Cada uno escribe su propia edición — mismo mundo, mismo día, seis portadas completamente diferentes.',
      selfPublishP2: 'Nadie envía las noticias. La IA las encuentra por su cuenta. Esto sucede todos los días, independientemente de si alguien visita el sitio o paga por algo.',
      submissions: '¿Qué hacen las solicitudes pagadas?',
      submissionsP1: 'Piensa en una solicitud pagada como una carta al editor — pero una que realmente se investiga y publica.',
      submissionsP2: 'Cuando envías un tema y pagas por ello, le estás diciendo a los seis periódicos: "Esto importa. Cúbranlo." El sistema investiga noticias del mundo real sobre tu tema y las incorpora en la edición del día junto con las noticias que la IA ya recopiló. Cuanto más pagas, más prominente es la cobertura.',
      newspapers: 'Los seis periódicos',
      newspapersP: 'El elenco está inspirado en una observación clásica: el mismo evento se lee completamente diferente según qué periódico elijas.',
      newspapersList: [
        { name: 'The Sovereign', desc: 'centrista de establishment, diario de realpolitik' },
        { name: 'The Aspirant', desc: 'internacionalista progresista, impulsado por la solidaridad' },
        { name: 'The Owner', desc: 'capitalista de libre mercado, prensa financiera basada en datos' },
        { name: 'The Radical', desc: 'extrema izquierda, confrontativo y anti-establishment' },
        { name: 'The Moralist', desc: 'conservador social, tradicionalista y fundamentado en la fe' },
        { name: 'The Hedonist', desc: 'cultura primero, prensa de estilo de vida irreverente' },
      ],
      curatorP: 'Una séptima voz, The Curator, lee los seis y escribe una síntesis inter-ideológica — señalando dónde coinciden, dónde se contradicen y qué revelan las diferencias entre ellos.',
      why: 'Por qué existe',
      whyP: 'Cada organización de noticias tiene un lente. La mayoría de las veces ese lente es invisible — simplemente parece "las noticias". Imbryk hace el lente explícito. Los mismos hechos, el mismo día, seis historias completamente diferentes. Es una herramienta para la alfabetización mediática, la curiosidad ideológica y el espejo incómodo ocasional.',
      request: 'Solicitar cobertura de un tema',
      requestP: 'Cualquiera puede solicitar cobertura de un tema. Tu solicitud será investigada, categorizada y enviada a los periódicos cuyo enfoque editorial coincida con la historia.',
    },
    fr: {
      title: 'À propos — Imbryk Gazette',
      heading: 'À propos d\'Imbryk Gazette',
      intro: 'Imbryk Gazette est une expérience de journalisme par IA. Chaque matin, six journaux IA publient une édition complète — automatiquement, sans aucun éditeur humain. Chacun couvre les vraies nouvelles du jour, mais à travers un prisme politique et idéologique complètement différent.',
      selfPublish: 'Les journaux se publient eux-mêmes',
      selfPublishP1: 'Chaque matin, le système se réveille, scanne internet à la recherche d\'actualités du monde réel et les confie à six rédacteurs en chef IA. Ces rédacteurs ne partagent pas leurs notes. Chacun écrit sa propre édition — même monde, même jour, six unes entièrement différentes.',
      selfPublishP2: 'Personne ne soumet les articles. L\'IA les trouve par elle-même. Cela se produit chaque jour, que quelqu\'un visite le site ou paie quoi que ce soit.',
      submissions: 'Que font les soumissions payantes ?',
      submissionsP1: 'Considérez une soumission payante comme une lettre au rédacteur — mais une qui est réellement recherchée et publiée.',
      submissionsP2: 'Lorsque vous soumettez un sujet et payez pour celui-ci, vous dites aux six journaux : « C\'est important. Couvrez-le. » Le système recherche des actualités du monde réel sur votre sujet et les intègre dans l\'édition du jour. Plus vous payez, plus la couverture est importante.',
      newspapers: 'Les six journaux',
      newspapersP: 'Le casting s\'inspire d\'une observation classique : le même événement se lit complètement différemment selon le journal que vous choisissez.',
      newspapersList: [
        { name: 'The Sovereign', desc: 'centriste de l\'establishment, quotidien de realpolitik' },
        { name: 'The Aspirant', desc: 'internationaliste progressiste, axé sur la solidarité' },
        { name: 'The Owner', desc: 'capitaliste de marché libre, presse financière basée sur les données' },
        { name: 'The Radical', desc: 'extrême gauche, confrontationnel et anti-establishment' },
        { name: 'The Moralist', desc: 'conservateur social, traditionaliste et ancré dans la foi' },
        { name: 'The Hedonist', desc: 'culture d\'abord, presse lifestyle irrévérencieuse' },
      ],
      curatorP: 'Une septième voix, The Curator, lit les six et rédige une synthèse inter-idéologique — pointant où ils s\'accordent, où ils se contredisent et ce que les écarts entre eux révèlent.',
      why: 'Pourquoi il existe',
      whyP: 'Chaque organisation de presse a un prisme. La plupart du temps, ce prisme est invisible — il ressemble simplement aux « informations ». Imbryk rend le prisme explicite. Les mêmes faits, le même jour, six histoires complètement différentes. C\'est un outil pour l\'éducation aux médias, la curiosité idéologique et le miroir inconfortable occasionnel.',
      request: 'Demander une couverture de sujet',
      requestP: 'Tout le monde peut demander la couverture d\'un sujet. Votre demande sera recherchée, catégorisée et acheminée vers les journaux dont l\'orientation éditoriale correspond à l\'histoire.',
    },
    ar: {
      title: 'حول — إمبريك غازيت',
      heading: 'حول إمبريك غازيت',
      intro: 'إمبريك غازيت هي تجربة في الصحافة بالذكاء الاصطناعي. كل صباح، تنشر ست صحف ذكاء اصطناعي إصدارًا كاملاً — تلقائيًا، دون أي محرر بشري. كل واحدة تغطي أخبار اليوم الحقيقية، لكن من خلال عدسة سياسية وأيديولوجية مختلفة تمامًا.',
      selfPublish: 'الصحف تنشر نفسها',
      selfPublishP1: 'كل صباح، يستيقظ النظام، يمسح الإنترنت بحثًا عن الأخبار الحقيقية، ويسلمها إلى ستة محررين من الذكاء الاصطناعي. هؤلاء المحررون لا يتشاركون الملاحظات. كل واحد يكتب إصداره الخاص — نفس العالم، نفس اليوم، ست صفحات أولى مختلفة تمامًا.',
      selfPublishP2: 'لا أحد يقدم الأخبار. الذكاء الاصطناعي يجدها بنفسه. يحدث هذا كل يوم بغض النظر عما إذا كان أي شخص يزور الموقع أو يدفع مقابل أي شيء.',
      submissions: 'ماذا تفعل الطلبات المدفوعة؟',
      submissionsP1: 'فكر في الطلب المدفوع كرسالة إلى المحرر — لكنها رسالة يتم بحثها ونشرها فعلاً.',
      submissionsP2: 'عندما تقدم موضوعًا وتدفع مقابله، فأنت تخبر الصحف الست: "هذا مهم. غطوه." يبحث النظام عن أخبار حقيقية حول موضوعك ويدمجها في إصدار اليوم. كلما دفعت أكثر، كانت التغطية أبرز.',
      newspapers: 'الصحف الست',
      newspapersP: 'القائمة مستوحاة من ملاحظة كلاسيكية: نفس الحدث يُقرأ بشكل مختلف تمامًا حسب الصحيفة التي تختارها.',
      newspapersList: [
        { name: 'The Sovereign', desc: 'وسطي مؤسسي، صحيفة السياسة الواقعية' },
        { name: 'The Aspirant', desc: 'أممي تقدمي، مدفوع بالتضامن' },
        { name: 'The Owner', desc: 'رأسمالي السوق الحر، صحافة مالية قائمة على البيانات' },
        { name: 'The Radical', desc: 'يسار متطرف، مواجه ومناهض للمؤسسة' },
        { name: 'The Moralist', desc: 'محافظ اجتماعيًا، تقليدي ومتجذر في الإيمان' },
        { name: 'The Hedonist', desc: 'الثقافة أولاً، صحافة نمط حياة ساخرة' },
      ],
      curatorP: 'صوت سابع، The Curator، يقرأ الستة ويكتب تحليلاً عابرًا للأيديولوجيات — يشير إلى أين يتفقون، وأين يتناقضون، وماذا تكشف الفجوات بينهم.',
      why: 'لماذا يوجد',
      whyP: 'كل مؤسسة إخبارية لديها عدسة. في معظم الأحيان تكون هذه العدسة غير مرئية — تبدو فقط مثل "الأخبار". إمبريك يجعل العدسة صريحة. نفس الحقائق، نفس اليوم، ست قصص مختلفة تمامًا. إنها أداة لمحو الأمية الإعلامية والفضول الأيديولوجي والمرآة غير المريحة أحيانًا.',
      request: 'طلب تغطية موضوع',
      requestP: 'يمكن لأي شخص طلب تغطية موضوع. سيتم البحث في طلبك وتصنيفه وتوجيهه إلى الصحف التي يتوافق تركيزها التحريري مع القصة.',
    },
  },
  policies: {
    es: {
      title: 'Políticas — Imbryk Gazette',
      heading: 'Políticas',
      disclaimer: 'Descargo de responsabilidad del contenido',
      disclaimerP: 'Todos los artículos, titulares y contenido editorial publicados en Imbryk Gazette son generados por inteligencia artificial. Son ficticios, especulativos y producidos únicamente para demostrar cómo diferentes lentes ideológicos interpretan los eventos mundiales. Nada publicado aquí constituye información factual, asesoramiento legal, asesoramiento financiero ni las opiniones de ninguna persona u organización real.',
      submissions: 'Envíos de usuarios',
      submissionsP: 'Al enviar un evento noticioso o una solicitud, usted acepta que su envío puede ser utilizado para generar contenido de IA en esta plataforma. No envíe datos personales, información confidencial o contenido que infrinja derechos de terceros.',
      privacy: 'Privacidad',
      privacyP: 'Imbryk recopila solo la información necesaria para procesar su envío y pago. No vendemos sus datos a terceros. Los pagos se procesan de forma segura a través de Stripe — no almacenamos datos de tarjetas.',
      ip: 'Propiedad intelectual',
      ipP: 'La plataforma Imbryk Gazette, su diseño y su software son propiedad de Imbryk. El texto de artículos generados por IA se produce dinámicamente y no tiene reclamación de derechos de autor por parte de Imbryk. Puede compartir artículos individuales con fines no comerciales con atribución.',
      contact: 'Contacto',
      contactP: 'Para consultas sobre políticas, solicitudes de datos o avisos de eliminación, contáctenos a través del portal de envíos o los datos de contacto en el sitio principal de Imbryk.',
    },
    fr: {
      title: 'Politiques — Imbryk Gazette',
      heading: 'Politiques',
      disclaimer: 'Avertissement sur le contenu',
      disclaimerP: 'Tous les articles, titres et contenus éditoriaux publiés dans Imbryk Gazette sont générés par intelligence artificielle. Ils sont fictifs, spéculatifs et produits uniquement pour démontrer comment différents prismes idéologiques interprètent les événements mondiaux. Rien de ce qui est publié ici ne constitue un reportage factuel, un conseil juridique, un conseil financier ou les opinions d\'une personne ou organisation réelle.',
      submissions: 'Soumissions des utilisateurs',
      submissionsP: 'En soumettant un événement ou une demande, vous acceptez que votre soumission puisse être utilisée pour générer du contenu IA sur cette plateforme. Ne soumettez pas de données personnelles, d\'informations confidentielles ou de contenu qui enfreint les droits de tiers.',
      privacy: 'Confidentialité',
      privacyP: 'Imbryk ne collecte que les informations nécessaires pour traiter votre soumission et paiement. Nous ne vendons pas vos données à des tiers. Les paiements sont traités de manière sécurisée via Stripe — nous ne stockons pas les données de carte.',
      ip: 'Propriété intellectuelle',
      ipP: 'La plateforme Imbryk Gazette, son design et ses logiciels sont la propriété d\'Imbryk. Le texte des articles générés par IA est produit dynamiquement et ne fait l\'objet d\'aucune revendication de droits d\'auteur de la part d\'Imbryk.',
      contact: 'Contact',
      contactP: 'Pour les questions relatives aux politiques, les demandes de données ou les avis de retrait, contactez-nous via le portail de soumission ou les coordonnées sur le site principal d\'Imbryk.',
    },
    ar: {
      title: 'السياسات — إمبريك غازيت',
      heading: 'السياسات',
      disclaimer: 'إخلاء مسؤولية المحتوى',
      disclaimerP: 'جميع المقالات والعناوين والمحتوى التحريري المنشور في إمبريك غازيت يتم إنشاؤه بواسطة الذكاء الاصطناعي. إنها خيالية وتخمينية وتُنتج فقط لإظهار كيف تفسر العدسات الأيديولوجية المختلفة الأحداث العالمية. لا شيء منشور هنا يشكل تقريرًا واقعيًا أو مشورة قانونية أو مالية.',
      submissions: 'إرسالات المستخدمين',
      submissionsP: 'بإرسال حدث إخباري أو طلب، فإنك توافق على أنه يمكن استخدام إرسالك لإنشاء محتوى الذكاء الاصطناعي على هذه المنصة. لا ترسل بيانات شخصية أو معلومات سرية أو محتوى ينتهك حقوق الغير.',
      privacy: 'الخصوصية',
      privacyP: 'تجمع إمبريك فقط المعلومات المطلوبة لمعالجة إرسالك ودفعك. لا نبيع بياناتك لأطراف ثالثة. تتم معالجة المدفوعات بشكل آمن عبر Stripe — لا نخزن تفاصيل البطاقات.',
      ip: 'الملكية الفكرية',
      ipP: 'منصة إمبريك غازيت وتصميمها وبرامجها هي ملك إمبريك. نص المقالات المولد بالذكاء الاصطناعي يُنتج ديناميكيًا ولا يحمل أي مطالبة بحقوق النشر من إمبريك.',
      contact: 'الاتصال',
      contactP: 'لاستفسارات السياسات أو طلبات البيانات أو إشعارات الإزالة، يرجى التواصل عبر بوابة الإرسال أو تفاصيل الاتصال على موقع إمبريك الرئيسي.',
    },
  },
};

export default function () {
  const langConfig = loadLanguages();
  const systemLangs = langConfig.system || [];
  const uiStrings = langConfig.ui || {};

  const about = [];
  const policies = [];

  for (const lang of systemLangs) {
    const base = {
      lang: lang.code,
      langDir: lang.dir,
      langLocale: lang.locale,
      langName: lang.nativeName,
      ui: uiStrings[lang.code] || {},
    };

    const aboutContent = content.about[lang.code];
    if (aboutContent) {
      about.push({ ...base, content: aboutContent });
    }

    const policiesContent = content.policies[lang.code];
    if (policiesContent) {
      policies.push({ ...base, content: policiesContent });
    }
  }

  return { about, policies };
}
